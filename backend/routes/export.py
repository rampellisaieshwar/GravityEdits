from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
from ..redis_config import q_render, q_videodb
from . import export  # Check circular import?? No, this is the file itself. 
# We don't need to import self.
# We need imports for file size checking logic if possible.

router = APIRouter()

# Directory Setup (Should match main.py or config)
UPLOAD_DIR = "uploads"
PROJECTS_DIR = "projects"
EXPORT_DIR = "exports"

class ExportRequest(BaseModel):
    project: dict 
    mode: Optional[str] = "local" 
    videodb_key: Optional[str] = None

def get_project_source_size(project_data):
    """
    Calculate total size of source files used in the project.
    """
    total_size = 0
    seen_files = set()
    
    clips = project_data.get('edl', [])
    for clip in clips:
        source_name = clip.get('source')
        if not source_name or source_name in seen_files:
            continue
            
        seen_files.add(source_name)
        
        # Try to find file
        # Logic copied/adapted from renderer.py path resolution would be best, 
        # but for now we look in UPLOAD_DIR and PROJECTS_DIR/name/source_media
        
        # 1. Uploads
        path = os.path.join(UPLOAD_DIR, source_name)
        if os.path.exists(path):
            total_size += os.path.getsize(path)
            continue
            
        # 2. Project Dir
        p_name = project_data.get('name', '')
        # Sanitize
        safe_name = "".join(c for c in p_name if c.isalnum() or c in (' ', '_', '-')).strip()
        path = os.path.join(PROJECTS_DIR, safe_name, "source_media", source_name)
        if os.path.exists(path):
            total_size += os.path.getsize(path)
            continue
            
        # 3. Fallback (heuristic search similar to renderer could go here, but keep it simple for traffic cop)

    return total_size / (1024 * 1024) # MB

def get_project_duration(project_data):
    """
    Calculate total duration of the project (kept clips).
    """
    total_duration = 0
    clips = project_data.get('edl', [])
    for clip in clips:
        # Check keep status
        keep = clip.get('keep', True)
        if isinstance(keep, str) and keep.lower() == 'false': keep = False
        
        if keep:
            dur = float(clip.get('duration', 0))
            total_duration += dur
    return total_duration

@router.post("/export-video/")
async def export_video(request: ExportRequest):
    mode = getattr(request, 'mode', 'local')
    
    if mode == "local":
        # Traffic Cop Checks
        try:
            duration = get_project_duration(request.project)
            size_mb = get_project_source_size(request.project)
            
            print(f"👮 Traffic Cop: Mode={mode}, Duration={duration}s, Size={size_mb:.2f}MB")
            
            if duration > 60 or size_mb > 50:
                 raise HTTPException(
                     status_code=400, 
                     detail="File too large for Free Tier (Max 60s / 50MB). Use Cloud Render."
                 )
                 
        except HTTPException as he:
            raise he
        except Exception as e:
            print(f"Traffic Cop Error: {e}")
            # If check fails, maybe let it slide or fail safe? 
            # Let's fail safe -> allow it but log warning, OR block.
            # Choosing to block if we are unsure to protect the server? 
            # No, if calculation fails, it might be a missing file, which renderer will handle.
            pass

        # Enqueue Local
        if not q_render:
             return {"error": "Render Service Unavailable (Redis Queue)"}
             
        job = q_render.enqueue(
            "backend.worker.tasks.perform_export_task",
            request.project, 
            EXPORT_DIR,
            job_timeout='1h'
        )
        return {"status": "queued", "job_id": job.id, "mode": "local"}

    elif mode == "cloud":
        # Enqueue Cloud (VideoDB)
        if not q_videodb:
             # Fallback to q_render if q_videodb not set up, but per instructions we use q_videodb
             if q_render:
                 print("⚠️ q_videodb unavailable, falling back to q_render for cloud task")
                 q_target = q_render
             else:
                 return {"error": "Render Service Unavailable"}
        else:
            q_target = q_videodb

        job = q_target.enqueue(
            "backend.worker.tasks.perform_videodb_export_task",
            request.project, 
            EXPORT_DIR,
            videodb_key=request.videodb_key,
            job_timeout='1h',
            at_front=True 
        )
        return {"status": "queued", "job_id": job.id, "mode": "cloud"}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {mode}")

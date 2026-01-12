from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import cv2
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid
import time
from datetime import datetime

# Import our modules
try:
    from . import ai_engine
    from . import renderer
    from . import chat_engine
except ImportError:
    import ai_engine
    import renderer
    import chat_engine

# Global job store
render_jobs: Dict[str, Any] = {}

def run_export_job(job_id: str, project_data: dict, output_dir: str):
    def progress_callback(data=None, **kwargs):
        if data is None: data = kwargs
        if not isinstance(data, dict): pass
        if isinstance(data, dict) and kwargs and data is not kwargs: data.update(kwargs)

        if job_id in render_jobs and isinstance(data, dict):
            render_jobs[job_id].update(data)
            
    try:
        render_jobs[job_id]["status"] = "processing"
        
        # Patch renderer if needed to support output_dir or just let it write to EXPORT_DIR and move?
        # For now, let's keep exports separate or move them.
        # Actually renderer writes to EXPORT_DIR by default. Let's leave strict projects structure for source/analysis for now.
        
        output_file_path = renderer.render_project(project_data, progress_callback=progress_callback)
        if output_file_path:
            filename = os.path.basename(output_file_path)
            # If we want scoped exports, we'd move it here. 
            # For simplicity, keep all exports in /exports for public access via static mount
            url = f"/exports/{filename}"
            render_jobs[job_id].update({"status": "completed", "url": url, "progress": 100, "message": "Render Complete"})
        else:
            render_jobs[job_id].update({"status": "failed", "message": "Rendering produced no output"})
    except Exception as e:
        print(f"Export Job Failed: {e}")
        import traceback
        traceback.print_exc()
        render_jobs[job_id].update({"status": "failed", "message": str(e)})

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory Setup
UPLOAD_DIR = "uploads" # Legacy bucket
PROJECTS_DIR = "projects"
EXPORT_DIR = "exports"

for d in [UPLOAD_DIR, PROJECTS_DIR, EXPORT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Mounts
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/exports", StaticFiles(directory=EXPORT_DIR), name="exports")
app.mount("/projects", StaticFiles(directory=PROJECTS_DIR), name="projects") # Expose project assets

# Utils
def get_video_duration(file_path):
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened(): return 0
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return duration
    except Exception as e:
        print(f"Error getting duration for {file_path}: {e}")
        return 0

def get_project_path(project_name):
    # Sanitize project name simple check
    safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '_', '-')).strip()
    return os.path.join(PROJECTS_DIR, safe_name)

# --- PROJECTS API ---

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

@app.get("/api/projects")
def list_projects():
    projects = []
    if os.path.exists(PROJECTS_DIR):
        for dirname in os.listdir(PROJECTS_DIR):
            path = os.path.join(PROJECTS_DIR, dirname)
            if os.path.isdir(path):
                # Try to read manifest
                manifest_path = os.path.join(path, "project.json")
                meta = {}
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r') as f: meta = json.load(f)
                    except: pass
                
                projects.append({
                    "name": dirname,
                    "created_at": meta.get("created_at"),
                    "thumbnail": meta.get("thumbnail"), # Could be path to first video thumb
                    "clip_count": len(os.listdir(os.path.join(path, "source_media"))) if os.path.exists(os.path.join(path, "source_media")) else 0
                })
    return projects

@app.post("/api/projects")
def create_project(data: ProjectCreate):
    path = get_project_path(data.name)
    if os.path.exists(path):
        raise HTTPException(status_code=400, detail="Project already exists")
    
    os.makedirs(path)
    os.makedirs(os.path.join(path, "source_media"))
    os.makedirs(os.path.join(path, "exports"))
    
    meta = {
        "name": data.name,
        "description": data.description,
        "created_at": datetime.now().isoformat(),
        "status": "created"
    }
    with open(os.path.join(path, "project.json"), "w") as f:
        json.dump(meta, f)
        
    return meta

@app.delete("/api/projects/{project_name}")
def delete_project(project_name: str):
    path = get_project_path(project_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        shutil.rmtree(path)
        return {"status": "deleted", "name": project_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Gravity Video Editor Backend"}

@app.post("/upload-batch/")
async def upload_batch(
    files: List[UploadFile] = File(...),
    project_name: Optional[str] = Form(None)
):
    uploaded_files = []
    
    # Determine target directory
    if project_name:
        # Sanitize!
        safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '_', '-')).strip()
        target_dir = os.path.join(get_project_path(safe_name), "source_media")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir) # Auto create if slightly out of sync
        # Also ensure simple mount access via /projects/name/source_media
        web_path_prefix = f"/projects/{project_name}/source_media"
    else:
        target_dir = UPLOAD_DIR
        web_path_prefix = "/uploads"

    print(f"Received {len(files)} files. Project: {project_name or 'None (Legacy)'}")
    
    for file in files:
        try:
            file_path = os.path.join(target_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            try:
                # Try getting video duration (opencv)
                duration = get_video_duration(file_path)
            except:
                duration = 0
            
            # If it's 0 and looks like audio, we can try moviepy later or just leave it
            # For now 0 is fine, Frontend handles it (defaulting to 5s visual or looping music)
            
            uploaded_files.append({
                "name": file.filename,
                "path": f"{web_path_prefix}/{file.filename}",
                "duration": duration
            })
            print(f"Successfully uploaded: {file.filename} ({duration}s) to {target_dir}")
        except Exception as e:
            print(f"Failed to upload {file.filename}: {str(e)}")
            pass
            
    return {"files": uploaded_files}

@app.get("/uploaded-videos/")
def list_uploaded_videos(project_name: Optional[str] = None):
    # This might need to support project scoping
    videos = []
    
    if project_name:
        target_dir = os.path.join(get_project_path(project_name), "source_media")
        web_path_prefix = f"/projects/{project_name}/source_media"
    else:
        target_dir = UPLOAD_DIR
        web_path_prefix = "/uploads"
        
    if os.path.exists(target_dir):
        for filename in os.listdir(target_dir):
            if filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                file_path = os.path.join(target_dir, filename)
                duration = get_video_duration(file_path)
                videos.append({
                    "name": filename,
                    "path": f"{web_path_prefix}/{filename}",
                    "duration": duration
                })
    return {"files": videos}

@app.get("/uploaded-audio/")
def list_uploaded_audio(project_name: Optional[str] = None):
    audio_files = []
    
    if project_name:
        target_dir = os.path.join(get_project_path(project_name), "source_media")
        web_path_prefix = f"/projects/{project_name}/source_media"
    else:
        target_dir = UPLOAD_DIR
        web_path_prefix = "/uploads"
        
    if os.path.exists(target_dir):
        for filename in os.listdir(target_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.aac', '.m4a')):
                file_path = os.path.join(target_dir, filename)
                # duration = get_audio_duration(file_path) # Future
                audio_files.append({
                    "name": filename,
                    "path": f"{web_path_prefix}/{filename}",
                    "type": "audio"
                })
    return {"files": audio_files}

class AnalyzeRequest(BaseModel):
    project_name: str
    file_names: List[str]
    description: Optional[str] = None
    api_key: Optional[str] = None

# Analysis job store
analysis_jobs: Dict[str, Any] = {}

def run_analysis_job(job_id: str, video_paths: List[str], project_name: str, output_dir: str, user_description: Optional[str] = None, api_key: str = None):
    try:
        analysis_jobs[job_id]["status"] = "processing"
        def progress_callback(progress, message):
            analysis_jobs[job_id]["progress"] = progress
            analysis_jobs[job_id]["message"] = message

        ai_engine.process_batch_pipeline(video_paths, project_name, output_dir=output_dir, progress_callback=progress_callback, user_description=user_description, api_key=api_key)
        analysis_jobs[job_id]["status"] = "completed"
        analysis_jobs[job_id]["progress"] = 100
    except Exception as e:
        print(f"Analysis Job Failed: {e}")
        import traceback
        traceback.print_exc()
        analysis_jobs[job_id].update({"status": "failed", "message": str(e)})

@app.post("/analyze/")
async def analyze_project(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    # Determine paths based on whether project exists in new structure
    project_path = get_project_path(request.project_name)
    
    # Force output to project directory
    if not os.path.exists(project_path):
        os.makedirs(project_path, exist_ok=True)
    output_dir = project_path

    if os.path.exists(os.path.join(project_path, "source_media")):
        source_dir = os.path.join(project_path, "source_media")
    else:
        # Fallback to uploads if not in new structure yet
        source_dir = UPLOAD_DIR

    # Construct full paths
    video_paths = [os.path.join(source_dir, fname) for fname in request.file_names]
    
    # Verify files exist and fix paths if needed
    verified_paths = []
    for path in video_paths:
        if not os.path.exists(path):
             # Fallback check for legacy mixing
             legacy_path = os.path.join(UPLOAD_DIR, os.path.basename(path))
             if source_dir != UPLOAD_DIR and os.path.exists(legacy_path):
                 verified_paths.append(legacy_path)
             else:
                 raise HTTPException(status_code=404, detail=f"File not found: {path}")
        else:
            verified_paths.append(path)
            
    video_paths = verified_paths

    # Run AI Pipeline
    job_id = str(uuid.uuid4())
    analysis_jobs[job_id] = {"status": "queued", "progress": 0, "message": "Queued"}
    
    print(f"DEBUG: Starting Analysis Job {job_id} with paths: {video_paths}")
    background_tasks.add_task(run_analysis_job, job_id, video_paths, request.project_name, output_dir, request.description, api_key=request.api_key)
    
    return {"status": "queued", "job_id": job_id, "message": "AI Analysis started"}

@app.get("/analysis-status/{job_id}")
async def get_analysis_status(job_id: str):
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return analysis_jobs[job_id]

@app.get("/api/projects/{project_name}/edl")
async def get_project_edl(project_name: str):
    # Check new project struct ONLY
    project_path = get_project_path(project_name)
    file_path = os.path.join(project_path, f"{project_name}.xml")
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='text/xml', filename=f"{project_name}.xml")
        
    return JSONResponse(status_code=404, content={"detail": f"EDL not found at {file_path}", "cwd": os.getcwd()})

@app.get("/api/projects/{project_name}/analysis")
async def get_project_analysis(project_name: str):
    project_path = get_project_path(project_name)
    file_path = os.path.join(project_path, f"{project_name}_analysis.json")
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/json')
    return JSONResponse(status_code=404, content={"detail": "Analysis not found yet"})

class ExportRequest(BaseModel):
    project: dict 

@app.post("/export-video/")
async def export_video(request: ExportRequest, background_tasks: BackgroundTasks):
    try:
        if hasattr(renderer, 'render_project'):
            job_id = str(uuid.uuid4())
            render_jobs[job_id] = {"status": "queued", "progress": 0, "message": "Queued"}
            
            # FUTURE: Pass output_dir if we want exports in project folder
            background_tasks.add_task(run_export_job, job_id, request.project, EXPORT_DIR)
            
            return {"status": "queued", "job_id": job_id}
        else:
             return {"error": "Renderer not implemented"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export-status/{job_id}")
async def get_export_status(job_id: str):
    if job_id not in render_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return render_jobs[job_id]

class ChatRequest(BaseModel):
    query: str
    project_name: str = None
    api_key: Optional[str] = None
    
@app.post("/chat/")
async def chat_with_ai(request: ChatRequest):
    context = None
    project_path = None
    
    # Determine Project Path and Context
    if request.project_name:
         # Standard Project Path
         p_path = get_project_path(request.project_name)
         project_path = p_path
         
         analysis_path = os.path.join(p_path, f"{request.project_name}_analysis.json")
         # Legacy fallback
         if not os.path.exists(analysis_path):
             legacy_path = os.path.join(UPLOAD_DIR, f"{request.project_name}_analysis.json")
             if os.path.exists(legacy_path):
                 analysis_path = legacy_path
             
         if os.path.exists(analysis_path):
             try:
                 with open(analysis_path, 'r') as f:
                     context = json.load(f)
             except Exception as e:
                 print(f"Failed to load analysis for chat context: {e}")
    else:
        # Default global chat
        project_path = os.path.join(PROJECTS_DIR, "_global_chat")

    # Delegate to Chat Engine (handles LangChain history internally)
    response = chat_engine.chat(request.query, context, project_path=project_path, api_key=request.api_key)
    
    return {"response": response}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

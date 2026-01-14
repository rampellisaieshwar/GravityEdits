import os
import traceback
from rq import get_current_job
from backend import renderer, ai_engine

def update_job_progress(progress=None, message=None, **kwargs):
    """Helper to update RQ job meta with progress info."""
    job = get_current_job()
    if not job:
        return

    meta_updated = False
    
    if progress is not None:
        job.meta['progress'] = progress
        meta_updated = True
        
    if message:
        job.meta['message'] = message
        meta_updated = True
        
    if kwargs:
        job.meta.update(kwargs)
        meta_updated = True
        
    if meta_updated:
        job.save_meta()

# --- TASK: EXPORT VIDEO ---
def perform_export_task(project_data, output_dir):
    job = get_current_job()
    print(f"🚀 Starting Export Task: Job {job.id if job else 'Unknown'}")
    
    # Send initial status
    update_job_progress(progress=0, status="processing", message="Starting Render...")
    
    def render_progress(data=None, **kwargs):
        # Adapt renderer callback (dict or kwargs) to RQ meta
        payload = {}
        if data and isinstance(data, dict):
            payload.update(data)
        if kwargs:
            payload.update(kwargs)
            
        # extract known fields for cleaner meta
        # POP them so they don't collide with explicit args or kwargs
        p = payload.pop('progress', None)
        m = payload.pop('message', None)
        s = payload.pop('status', None) 
        
        # Update job meta
        # Pass 'status' in kwargs explicitly if it exists, or let it be in payload?
        # Since 'status' is NOT in update_job_progress signature, it must go in kwargs.
        # But we popped it. So let's put it back in kwargs via explicit arg if present.
        
        extra_args = payload
        if s:
            extra_args['status'] = s
            
        update_job_progress(progress=p, message=m, **extra_args)

    try:
        # Run the renderer
        # Note: renderer.render_project writes to file and returns path
        output_file_path = renderer.render_project(project_data, progress_callback=render_progress)
        
        if output_file_path:
            filename = os.path.basename(output_file_path)
            # URL relative to static mount
            url = f"/exports/{filename}"
            
            # Final Success Update
            update_job_progress(
                progress=100, 
                status="completed", 
                message="Render Complete", 
                url=url, 
                output_path=output_file_path
            )
            return url
        else:
            update_job_progress(status="failed", message="Rendering produced no output")
            raise Exception("Rendering produced no output")
            
    except Exception as e:
        print(f"❌ Export Task Failed: {e}")
        traceback.print_exc()
        update_job_progress(status="failed", message=str(e))
        raise e


# --- TASK: AI ANALYSIS ---
def perform_analysis_task(video_paths, project_name, output_dir, user_description=None, api_key=None):
    job = get_current_job()
    print(f"🧠 Starting Analysis Task: Job {job.id if job else 'Unknown'}")
    
    update_job_progress(progress=0, status="processing", message="Initializing AI Engine...")
    
    def analysis_progress(progress, message):
        # Adapt analysis callback (progress int, message str)
        update_job_progress(progress=progress, message=message)

    try:
        ai_engine.process_batch_pipeline(
            video_paths, 
            project_name, 
            output_dir=output_dir, 
            progress_callback=analysis_progress, 
            user_description=user_description, 
            api_key=api_key
        )
        
        # Final Success Update
        update_job_progress(progress=100, status="completed", message="Analysis Complete")
        return True
        
    except Exception as e:
        print(f"❌ Analysis Task Failed: {e}")
        traceback.print_exc()
        update_job_progress(status="failed", message=str(e))
        raise e

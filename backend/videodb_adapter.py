
import os
import videodb
import time
import traceback
from videodb import timeline, TextStyle

class VideoDBAdapter:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("VIDEODB_API_KEY")
        if not self.api_key:
             # Fallback to the user provided key for testing if env is missing
             self.api_key = "sk-IJCQabycCipdvdJf_QR53NZuFPdU7SdfIFXRN6DF6sg"
        
        try:
            self.conn = videodb.connect(api_key=self.api_key)
            try:
                self.coll = self.conn.get_collection("gravity_edits_default")
            except Exception:
                print("Collection not found, creating new one...")
                self.coll = self.conn.create_collection("gravity_edits_default", "Default collection for Gravity Edits")
                
        except Exception as e:
            print(f"❌ Failed to connect to VideoDB: {e}")
            traceback.print_exc()
            self.coll = None

    def _resolve_source_path(self, source_name, project_name=""):
        # Uploads folder (Legacy)
        UPLOAD_DIR = "uploads"
        source_path = os.path.join(UPLOAD_DIR, os.path.basename(source_name))
        
        # Priority 2: Project Specific Folder
        if not os.path.exists(source_path):
             # Try exact name
             safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '_', '-')).strip()
             project_media_path = os.path.join("projects", safe_name, "source_media", os.path.basename(source_name))
             
             if os.path.exists(project_media_path):
                 source_path = project_media_path
        
        # Fallback 1: Scan all project folders
        if not os.path.exists(source_path):
             if os.path.exists("projects"):
                for dirname in os.listdir("projects"):
                    possible_path = os.path.join("projects", dirname, "source_media", os.path.basename(source_name))
                    if os.path.exists(possible_path):
                        source_path = possible_path
                        break
        
        # Fallback 2: Absolute
        if not os.path.exists(source_path):
             # Try absolute path from previous logs
             abs_fallback = os.path.join("/Users/saieshwarrampelli/Downloads/GravityEdits/source_media", os.path.basename(source_name))
             if os.path.exists(abs_fallback):
                  source_path = abs_fallback

        return source_path if os.path.exists(source_path) else None

    def render_project(self, project_data, progress_callback=None):
        if not self.coll:
            raise Exception("VideoDB Connection not initialized")

        print("☁️ Starting VideoDB Cloud Render...")
        if progress_callback:
            progress_callback({"status": "processing", "progress": 10, "message": "Connecting to Cloud..."})

        # 1. Ingest Assets
        asset_map = {} # filename -> Video object
        
        clips_list = project_data.get('edl', project_data.get('clips', []))
        files_to_upload = set()
        
        for clip in clips_list:
            files_to_upload.add(clip['source'])
            
        total_uploads = len(files_to_upload)
        
        for i, filename in enumerate(files_to_upload):
            if filename in asset_map: continue
            
            # Resolve path
            local_path = self._resolve_source_path(filename, project_data.get('name', ''))
            

            # 1. Upload Assets
            try:
                videos = self.coll.get_videos(name=filename)
                if videos:
                    video = videos[0]
                    print(f"   ✅ Found cached asset: {video.id}")
                    
                    # CLOUD REFRAME (Cached)
                    if project_data.get('renderMode') == 'portrait':
                        print(f"📱 Cloud Reframe: Converting cached {filename} to vertical...")
                        try:
                            # Use simple simple crop for reliability and speed matching local behavior
                            # or use 'smart' if we want AI. Using generic 'vertical' (smart default)
                            # to leverage VideoDB capabilities as requested.
                            video = video.reframe(target="vertical", mode="simple")
                        except Exception as e:
                            print(f"⚠️ Reframe failed (using original): {e}")

                    asset_map[filename] = video
                    continue
            except:
                pass 

            if not local_path:
                print(f"⚠️ Source file missing: {filename}")
                continue
                
            print(f"☁️ Uploading {filename} to VideoDB...")
            if progress_callback:
                progress_callback({"status": "processing", "progress": 10 + (i/total_uploads)*30, "message": f"Uploading {filename}..."})
            
            try:
                # Upload with name
                video = self.coll.upload(file_path=local_path)
                
                # CLOUD REFRAME (New Upload)
                if project_data.get('renderMode') == 'portrait':
                    print(f"📱 Cloud Reframe: Converting new {filename} to vertical...")
                    try:
                         # mode="simple" for Center Crop (Predictable)
                         video = video.reframe(target="vertical", mode="simple")
                    except Exception as e:
                         print(f"⚠️ Reframe failed (using original): {e}")

                asset_map[filename] = video
            except Exception as e:
                print(f"❌ Upload failed: {e}")
                raise e

        # 2. Build Timeline
        print("☁️ Building Cloud Timeline...")
        if progress_callback:
            progress_callback({"status": "processing", "progress": 50, "message": "Building Stream..."})
        
        try:
            # Create Timeline
            t_line = timeline.Timeline(self.conn)
            
            has_video = False
            
            # Add Clips
            for i, clip_data in enumerate(clips_list):
                if clip_data.get('keep') is False: continue
                
                filename = clip_data['source']
                video = asset_map.get(filename)
                if not video: continue
                
                # Resolve local duration for fallback if needed
                local_path = self._resolve_source_path(filename, project_data.get('name', ''))
                
                start = float(clip_data.get('start', 0))
                end = float(clip_data.get('end', 0))
                
                # Duration logic for 'end'
                if end == 0:
                    duration = 0
                    if hasattr(video, 'duration'): duration = float(video.duration)
                    elif hasattr(video, 'length'): duration = float(video.length)
                    
                    if duration == 0 and local_path:
                        try:
                            import cv2
                            cap = cv2.VideoCapture(local_path)
                            if cap.isOpened():
                                fps = cap.get(cv2.CAP_PROP_FPS)
                                fc = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                                if fps > 0: duration = fc / fps
                                cap.release()
                        except: pass
                    
                    if duration == 0: duration = 10.0 # Default
                    end = duration

                # VideoAsset
                # VideoDB 'start'/'end' are trim points in the source video
                v_asset = timeline.VideoAsset(asset_id=video.id, start=start, end=end)
                t_line.add_inline(v_asset)
                has_video = True
            
            if not has_video:
                 print("⚠️ No clips found for timeline. Timeline empty.")
                 # If empty, maybe just return or add a dummy?
                 # Raising error crashes the worker.
                 if progress_callback:
                    progress_callback({"status": "failed", "message": "No valid clips selected for export."})
                 return None
            
            # 3. Add Overlays
            overlays = project_data.get('overlays', [])
            for ov in overlays:
                content = ov.get('content', '')
                t_start = float(ov.get('start', 0)) # Timeline start time
                t_dur = float(ov.get('duration', 2))
                
                # Parse Frontend Properties
                # FontSize (0-1 normalized)
                f_size_pct = ov.get('fontSize', 0.05)
                try:
                    f_norm = float(f_size_pct)
                    if f_norm > 1.0: f_norm /= 100.0
                except: f_norm = 0.05
                
                # Assume 1080p canvas for reference calculation since VideoDB handles scaling usually
                # or we just provide a reasonable int.
                # Renderer uses Height * norm * 1.5. Let's use 1080 as Ref Height.
                calc_fontsize = int(1080 * f_norm * 1.5)
                if calc_fontsize < 40: calc_fontsize = 40
                
                # Position (0-1 normalized)
                p_x = ov.get('positionX', 0.5)
                p_y = ov.get('positionY', 0.8)
                try:
                     pos_x = float(p_x)
                     pos_y = float(p_y)
                     if pos_x > 1.0: pos_x /= 100.0
                     if pos_y > 1.0: pos_y /= 100.0
                except:
                     pos_x, pos_y = 0.5, 0.8

                # Color
                t_color = ov.get('textColor', 'white')
                
                # VideoDB Expressions:
                # x = (main_w - text_w) * pos_x
                # y = (main_h - text_h) * pos_y
                # We format this as a string for VideoDB runtime evaluation
                expr_x = f"(main_w-text_w)*{pos_x:.2f}"
                expr_y = f"(main_h-text_h)*{pos_y:.2f}"

                style = TextStyle(
                    fontsize=calc_fontsize, 
                    fontcolor=t_color,
                    x=expr_x,
                    y=expr_y,
                    box=True,
                    boxcolor='black',
                    boxborderw='5'
                )
                
                t_asset = timeline.TextAsset(text=str(content), duration=t_dur, style=style)
                
                # add_overlay(start_time, asset)
                t_line.add_overlay(t_start, t_asset)

            # 4. Generate Stream
            print("☁️ Rendering on Cloud...")
            if progress_callback:
                progress_callback({"status": "processing", "progress": 80, "message": "Cloud Rendering..."})
            
            stream_url = t_line.generate_stream()
            print(f"☁️ Stream Generated: {stream_url}")
            
            # 5. Download HLS to MP4 (Hybrid Workflow)
            # Use `yt_dlp` for robust HLS downloading with retries
            if progress_callback:
                progress_callback({"status": "processing", "progress": 90, "message": "Finalizing MP4 File (v2)..."})
                
            timestamp = int(time.time())
            filename = f"{project_data.get('name', 'project')}_cloud_{timestamp}.mp4"
            output_path = os.path.join("exports", filename)
            
            print(f"☁️ Downloading Stream to {output_path}...")
            
            try:
                import yt_dlp
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': output_path,
                    'fragment_retries': 50,
                    'retries': 20,
                    'socket_timeout': 60,
                    'ignoreerrors': True,
                    'concurrent_fragment_downloads': 1,
                    'quiet': True, 
                    'no_warnings': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([stream_url])
                
                # Check for Portrait Mode Crop
                if project_data.get('renderMode') == 'portrait' and os.path.exists(output_path):
                    print("📱 Transforming to Portrait (9:16)...")
                    if progress_callback:
                         progress_callback({"status": "processing", "progress": 95, "message": "Converting to Portrait..."})
                    
                    cropped_path = output_path.replace(".mp4", "_cropped.mp4")
                    # ffmpeg crop=ih*(9/16):ih,scale=1080:1920
                    cmd = [
                        "ffmpeg", "-y", "-i", output_path,
                        "-vf", "crop=ih*(9/16):ih,scale=1080:1920:flags=lanczos", 
                        "-c:a", "copy",
                        cropped_path
                    ]
                    import subprocess
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if os.path.exists(cropped_path):
                        os.remove(output_path)
                        os.rename(cropped_path, output_path)
                        print("✅ Portrait Crop & Upscale Complete")

            except Exception as e:
                 print(f"DL Error: {e}")
                 # Fallback?
                 raise e
                
            print(f"✅ Downloaded MP4: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ Timeline Generation failed: {e}")
            traceback.print_exc()
            raise e


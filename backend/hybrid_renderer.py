import os
import subprocess
from moviepy import VideoFileClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
import traceback
import time

# Try to import from renderer, assuming it's in the same package
# We use conditional import or try/except to handle running as script vs module
try:
    from backend.renderer import create_motion_text, RenderLogger
except ImportError:
    try:
        from renderer import create_motion_text, RenderLogger
    except ImportError:
        # Fallback if we can't find it
        print("⚠️ Warning: Could not import renderer.create_motion_text")
        create_motion_text = None

# Robust audio_loop import (same as renderer.py)
try:
    from moviepy.audio.fx.all import audio_loop
except ImportError:
    try:
        from moviepy.audio.fx.audio_loop import audio_loop
    except ImportError:
        # Manual implementation if missing
        from moviepy.audio.AudioClip import concatenate_audioclips
        def audio_loop(audioclip, duration=None, n=None):
            if duration is not None:
                n = int(duration / audioclip.duration) + 1
            elif n is None:
                n = 1
            clips = [audioclip] * n
            new_clip = concatenate_audioclips(clips)
            if duration is not None:
                new_clip = new_clip.subclipped(0, duration)
            return new_clip

TEMP_DIR = "temp_assets"

def ensure_temp_dir():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    return TEMP_DIR

def resolve_source_path(source_name, project_data, upload_dir="uploads"):
    """
    Replicates the path resolution logic from renderer.py
    """
    # Priority 1: Uploads folder
    source_path = os.path.join(upload_dir, os.path.basename(source_name))
    
    # Priority 2: Project Specific Folder
    if not os.path.exists(source_path):
        p_name = project_data.get('name', '')
        safe_name = "".join(c for c in p_name if c.isalnum() or c in (' ', '_', '-')).strip()
        project_media_path = os.path.join("projects", safe_name, "source_media", os.path.basename(source_name))
        
        if os.path.exists(project_media_path):
            source_path = project_media_path
        else:
            # Try heuristic for Shorts
            parts = safe_name.split('_')
            if len(parts) > 1:
                base_name = parts[0]
                heuristic_path = os.path.join("projects", base_name, "source_media", os.path.basename(source_name))
                if os.path.exists(heuristic_path):
                    source_path = heuristic_path

    # Priority 3: Absolute Fallback
    if not os.path.exists(source_path):
        abs_fallback = os.path.join("/Users/saieshwarrampelli/Downloads/GravityEdits/source_media", os.path.basename(source_name))
        if os.path.exists(abs_fallback):
            source_path = abs_fallback
        
        # Priority 4: Search blindly (Extension fix)
        if not os.path.exists(source_path) and '.' not in source_name:
            for ext in ['.mp4', '.mov', '.mkv']:
                test_path = source_path + ext
                if os.path.exists(test_path):
                    source_path = test_path
                    break
    
    return source_path

def generate_text_overlay_asset(overlay_data, base_size, idx):
    """
    Generates a transparent video file for a text overlay.
    """
    try:
        content = overlay_data.get('content', '')
        start = float(overlay_data.get('start', 0))
        dur = float(overlay_data.get('duration', 2.0))
        style = overlay_data.get('style', 'pop')
        
        f_size = overlay_data.get('fontSize')
        p_x = overlay_data.get('positionX')
        p_y = overlay_data.get('positionY')
        t_color = overlay_data.get('textColor', 'white')
        font_fam = overlay_data.get('fontFamily', 'Arial-Bold')
        
        mult = 1.0
        if f_size is not None:
            try:
                mult = float(f_size) / 4.0
            except: pass
            
        custom_pos = None
        if p_x is not None and p_y is not None:
            try:
                custom_pos = (float(p_x)/100.0, float(p_y)/100.0)
            except: pass
        
        # Safe Max Width
        max_w = int(base_size[0] * 0.8) if base_size else 1000

        txt_clip = create_motion_text(
            content, 
            duration=dur, 
            style=style, 
            fontsize_mult=mult, 
            pos=custom_pos, 
            color=t_color, 
            font=font_fam, 
            max_width=max_w
        )
        
        if not txt_clip:
            print(f"⚠️ TextClip failed for overlay {idx}. Using RED BOX fallback.")
            from moviepy.video.VideoClip import ColorClip
            # Create a Red Box 500x100
            txt_clip = ColorClip(size=(500, 100), color=(255, 0, 0), duration=dur)
            # We can't easily add text 'ERROR' without TextClip, so just Red Box.
        
        # 2. THE FIX: Explicit Duration on Clip
        txt_clip = txt_clip.with_duration(dur)
        
        # 3. THE FIX: Composite Logic
        w, h = base_size
        
        # We must place the text on a transparent canvas
        final_clip = CompositeVideoClip(
            [txt_clip], 
            size=(w, h), 
            bg_color=None, # Transparent
            use_bgclip=False 
        ).with_duration(dur) # <--- CRITICAL: Set duration on the Composite

        output_path = os.path.join(ensure_temp_dir(), f"overlay_{idx}.mov")
        
        # 4. Render with Alpha
        final_clip.write_videofile(
            output_path, 
            fps=30, # Match project FPS (User snippet said 24, but 30 is safer for sync)
            codec="png", # 'png' is safer for Alpha than prores_ks on some systems
            ffmpeg_params=['-pix_fmt', 'rgba'], # Ensures Alpha Channel is written
            logger="bar"
        )
        
        # DEBUG: Check if file exists and has size
        if os.path.exists(output_path):
             sz = os.path.getsize(output_path)
             print(f"  - Generated Overlay {idx}: {output_path} ({sz} bytes)")
        else:
             print(f"  - ⚠️ Failed to generate {output_path}")
        
        return output_path, start, dur
    
    except Exception as e:
        print(f"Failed to generate text asset {idx}: {e}")
        traceback.print_exc()
        return None

def build_ffmpeg_filter_complex(clips_info, text_assets, total_duration, base_res=(1920, 1080)):
    """
    Constructs the filter_complex string for FFmpeg.
    clips_info: list of dict {path, start, end, grading}
    text_assets: list of tuples (path, start, dur)
    base_res: tuple (width, height) target resolution
    """
    inputs = []
    filter_chains = []
    concat_inputs = []
    
    # 1. Process Main Video Clips
    for i, clip in enumerate(clips_info):
        inputs.append("-i")
        inputs.append(clip['path'])
        
        # Filter Chain for this clip
        # [i:v]trim=start=S:end=E,setpts=PTS-STARTPTS,eq=...[v_i]
        
        # Grading
        grading = clip.get('grading', {})
        filters = []
        
        # Trim
        # Note: FFmpeg trim takes input stream time. 
        # clip['start'] and clip['end'] from user JSON refer to the SOURCE file timestamps
        # So `trim=start=X:end=Y` works perfectly.
        start = clip['start']
        end = clip['end']
        filters.append(f"trim=start={start}:end={end}")
        filters.append("setpts=PTS-STARTPTS")
        
        # Grading Eq
        # eq=contrast=...:brightness=...:saturation=...
        # Map our numpy grading to eq/colorbalance
        # Temp -> colorbalance?
        grade_filts = []
        
        con = float(grading.get('contrast', 0))
        # numpy: (img - 128) * factor + 128. approx mapping?
        # ffmpeg eq: contrast=1.0 is neutral.
        # our numpy: factor = 1 + (con/100).
        c_val = 1.0 + (con / 100.0)
        
        sat = float(grading.get('saturation', 100))
        s_val = sat / 100.0
        
        exp = float(grading.get('exposure', 0))
        # exposure in ev? eq brightness is additive shift.
        # eq doesn't have exposure. colorlevels or curves?
        # approximate with brightness? No, exposure is mult.
        # eq has gamma?
        # Let's simple mapping: brightness shift?
        # exposure=1 -> double signal. brightness=0.1?
        # Let's skip precise exposure mapping for now or use gamma.
        # Actually `eq` has `contrast, brightness, saturation, gamma`.
        
        if c_val != 1.0 or s_val != 1.0:
            grade_filts.append(f"eq=contrast={c_val}:saturation={s_val}")
            
        # Temperature (Kelvin)
        # Using `colortemperature` if available, or `colorbalance`
        temp = float(grading.get('temperature', 5600))
        if temp != 5600:
            # Simple shifting red/blue
            # > 5600 -> Warm (Red up, Blue down)
            # < 5600 -> Cool (Red down, Blue up)
            # colorbalance ranges -1.0 to 1.0
            shift = (temp - 5600) / 10000.0 # Arbitrary scaling
            # Clamp
            shift = max(-1.0, min(1.0, shift))
            # If shift > 0 (Warm): rs=+shift, bs=-shift
            grade_filts.append(f"colorbalance=rs={shift}:bs={-shift}:rm={shift}:bm={-shift}:rh={shift}:bh={-shift}")

        if grade_filts:
            filters.extend(grade_filts)
        
        # Scale to common resolution?
        # If we assume 1080p source, fine. If mixed, we should scale.
        # Let's force scale to 1920:1080 to be safe?
        # filters.append("scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2")
        # For now assume mostly uniform or handle later. 
        # Adding scale avoids concatenation errors.
        # Scale to common resolution matches base_res
        # Force scaling to avoid concatenation errors
        w_target, h_target = base_res
        filters.append(f"scale={w_target}:{h_target}") 
        filters.append("setsar=1") # reset sample aspect ratio to square pixels prevents issues
        
        chain = ",".join(filters)
        filter_chains.append(f"[{i:d}:v]{chain}[v{i}]")
        concat_inputs.append(f"[v{i}]")
        
    # Concat
    # [v0][v1]concat=n=N:v=1:a=0[base]
    concat_str = "".join(concat_inputs)
    filter_chains.append(f"{concat_str}concat=n={len(clips_info)}:v=1:a=0[vbase]")
    
    # 2. Process Overlays
    # Input indices for overlays start at len(clips_info)
    current_v_label = "vbase"
    
    text_input_start_idx = len(clips_info)
    
    # We also have an Audio Input at the very end.
    # So text inputs are from text_input_start_idx to text_input_start_idx + len(text_assets) - 1
    
    for j, (path, start, dur) in enumerate(text_assets):
        idx = text_input_start_idx + j
        
        # Standard Input (No offset on input level)
        inputs.append("-i")
        inputs.append(path)
        
        # Overlay Logic with setpts
        # [curr][idx]overlay...
        next_label = f"vov{j}"
        
        start_f = float(start)
        end_f = start_f + float(dur)
        
        # 1. Delay the overlay stream to start time
        # We need to shift PTS.
        # Note: If input is 2s long. PTS starts at 0.
        # We want it to start at `start_f`.
        # setpts=PTS+START_SECONDS/TB
        
        delay_label = f"vov_delayed_{j}"
        filter_chains.append(f"[{idx}:v]setpts=PTS+({start_f:.3f}/TB)[{delay_label}]")
        
        # 2. Overlay it
        # enable is still useful to ensure it disappears/appears cleanly
        filter_chains.append(f"[{current_v_label}][{delay_label}]overlay=enable='between(t,{start_f:.3f},{end_f:.3f})':eof_action=pass[vov{j}]")
        current_v_label = next_label
        
    final_output_label = current_v_label
    
    return inputs, filter_chains, final_output_label

def render_hybrid_project(project_data, progress_callback=None):
    print("🚀 Starting Hybrid Render (MoviePy + FFmpeg)...")
    ensure_temp_dir()
    
    upload_dir = "uploads"
    # Find resolution from first valid clip
    base_res = (1920, 1080) # Default
    try:
        # Check first a few clips until we find one
        for c in project_data.get('edl', project_data.get('clips', []))[:3]:
             src = resolve_source_path(c.get('source', ''), project_data, upload_dir)
             if os.path.exists(src):
                 with VideoFileClip(src) as v:
                     # Check rotation
                     if v.rotation in [90, 270]:
                         base_res = (v.h, v.w)
                     else:
                         base_res = (v.w, v.h)
                     print(f"Detected Base Resolution: {base_res}")
                     break
    except Exception as e:
        print(f"Warning: Could not detect resolution: {e}")
    
    clips_list = project_data.get('edl', project_data.get('clips', []))
    processed_clips_info = []
    
    # 1. Gather Clips & Prepare Audio
    # We use MoviePy to handle audio logic because it's complex (mixing, split, loop)
    # and fast enough for audio.
    
    audio_clips = []
    
    # A. Source Audio
    print("🔊 processing audio...")
    if progress_callback: progress_callback({"status": "processing", "progress": 5, "message": "Processing audio..."})

    for i, clip_data in enumerate(clips_list):
        keep = clip_data.get('keep', True)
        if isinstance(keep, str) and keep.lower() == 'false': keep = False
        if not keep: continue
        
        src_path = resolve_source_path(clip_data['source'], project_data, upload_dir)
        if not os.path.exists(src_path): continue
        
        start = float(clip_data.get('start', 0))
        # Logic for end/duration
        end_val = clip_data.get('end')
        if not end_val or float(end_val) == 0:
            dur = float(clip_data.get('duration', 0))
            if dur > 0: end_val = start + dur
            else: 
                # Need to know file duration. 
                # Expensive to open each? Just use ffmpeg probe or existing knowledge?
                # We'll trust provided duration or open quickly
                with VideoFileClip(src_path) as v:
                    end_val = v.duration
        
        end = float(end_val)
        
        # Use Exact Cut Times (No Buffer)
        # The user wants exact EDL cuts.
        safe_start = start
        safe_end = end
        
        # Validation
        if safe_start >= safe_end:
             # Fallback if invalid
             print(f"⚠️ Invalid clip times for {i}: {safe_start} to {safe_end}. Skipping.")
             continue
        
        # Let's open clip for audio
        try:
             # Just audio
             # Note: AudioFileClip reads the file.
             audioclip = AudioFileClip(src_path)
             
             # Safety Clamp
             if safe_end > audioclip.duration:
                 safe_end = audioclip.duration
                 
             if safe_start >= safe_end:
                 continue

             # Cut
             sub = audioclip.subclipped(safe_start, safe_end)
             audio_clips.append(sub)
             
             # Store info for Video FFmpeg
             processed_clips_info.append({
                 "path": src_path,
                 "start": safe_start,
                 "end": safe_end,
                 "grading": clip_data.get('colorGrading', {})
             })
             
        except Exception as e:
            print(f"Audio prep error clip {i}: {e}")

    # B. BG Music & SFX (Reuse logic via manual implementation simplified)
    # ... We can copy the logic from renderer.py or try to be generic
    # For now, let's just implement the BG Music part simply
    
    bg_music_config = project_data.get('bgMusic')
    if bg_music_config and bg_music_config.get('source'):
        try:
            m_path = resolve_source_path(bg_music_config['source'], project_data, upload_dir)
            if os.path.exists(m_path):
                bg = AudioFileClip(m_path)
                bg = bg.multiply_volume(float(bg_music_config.get('volume', 0.5)))
                # Loop/Cut logic... skipping complex loop for brevity in this step, taking full length
                # Calculate total duration of video
                total_video_dur = sum([c['end'] - c['start'] for c in processed_clips_info])
                if bg.duration < total_video_dur:
                    bg = audio_loop(bg, duration=total_video_dur)
                else:
                    bg = bg.subclipped(0, total_video_dur)
                
                bg = bg.with_start(float(bg_music_config.get('start', 0)))
                audio_clips.append(bg)
        except Exception as e:
            print(f"BG Music Error: {e}")

    # Mix Audio
    final_audio_path = os.path.join(ensure_temp_dir(), "mixed_audio.m4a")
    if audio_clips:
        # Concatenate source audio clips?
        # Wait, source audio clips correspond to video clips in sequence.
        # But we added them to a flat list `audio_clips`.
        # `CompositeAudioClip` mixes them all starting at 0 unless `set_start` is used.
        # Source audio must be concatenated in sequence.
        # BG music overlayed.
        
        # Separate source vs overlay
        # The first N clips are source clips. They should be concatenated.
        num_source = len(processed_clips_info)
        source_audio_parts = audio_clips[:num_source]
        overlay_audio_parts = audio_clips[num_source:]
        
        from moviepy.audio.AudioClip import concatenate_audioclips
        try:
            main_track = concatenate_audioclips(source_audio_parts)
            final_mix_list = [main_track]
            final_mix_list.extend(overlay_audio_parts)
            
            final_audio = CompositeAudioClip(final_mix_list)
            final_audio.write_audiofile(final_audio_path, logger=None)
        except Exception as e:
            print(f"Audio Mixing Error: {e}")
            final_audio_path = None
    else:
        final_audio_path = None

    # 2. Convert Overlays to Assets
    print("✨ Generating Text Overlays (MoviePy)...")
    if progress_callback: progress_callback({"status": "processing", "progress": 20, "message": "Generating Text..."})
    
    overlays = project_data.get('overlays', [])
    text_assets = []
    for i, ov in enumerate(overlays):
        res = generate_text_overlay_asset(ov, base_res, i)
        if res:
            text_assets.append(res)
            
    # 3. Build FFmpeg Command
    print("🎬 Assembling Video (FFmpeg)...")
    if progress_callback: progress_callback({"status": "processing", "progress": 40, "message": "Assembling Video..."})
    
    inputs, filter_chains, last_v_label = build_ffmpeg_filter_complex(
        processed_clips_info, 
        text_assets, 
        0, # Duration handled by concat
        base_res
    )
    
    # 4. Construct Final Command
    # Inputs...
    # Then Audio Input (if exists)
    audio_input_idx = -1
    if final_audio_path and os.path.exists(final_audio_path):
        inputs.append("-i")
        inputs.append(final_audio_path)
        audio_input_idx = (len(inputs) // 2) - 1
    
    # Filter Complex file (to avoid char limit)
    fc_script = ";".join(filter_chains)
    fc_path = os.path.join(ensure_temp_dir(), "filter_script.txt")
    with open(fc_path, "w") as f:
        f.write(fc_script)
        
    output_filename = f"{project_data.get('name', 'video')}_hybrid_{int(time.time())}.mp4"
    output_path = os.path.join("exports", output_filename)
    
    cmd = ["ffmpeg", "-y"]
    cmd.extend(inputs)
    cmd.extend(["-filter_complex_script", fc_path])
    
    # Mapping
    cmd.extend(["-map", f"[{last_v_label}]"])
    if audio_input_idx >= 0:
        cmd.extend(["-map", f"{audio_input_idx}:a"])
        
    cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac"])
    cmd.extend([output_path])
    
    print(f"Running FFmpeg: {' '.join(cmd)}")
    
    # Execute
    # Calculate Total Duration for Progress
    total_duration = sum([c['end'] - c['start'] for c in processed_clips_info])
    if total_duration == 0: total_duration = 1.0

    print(f"Running FFmpeg (Duration: {total_duration:.2f}s): {' '.join(cmd)}")
    
    import re
    # Regex to capture "time=00:00:00.00"
    time_regex = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
    
    # Execute with stderr pipe
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.DEVNULL, # Ignore stdout
        stderr=subprocess.PIPE,    # Read progress from stderr
        universal_newlines=True,
        bufsize=1 # Line buffered
    )
    
    # Real-time Progress Monitoring
    while True:
        # Read line from stderr
        line = process.stderr.readline()
        
        # Check if process finished
        if not line and process.poll() is not None:
            break
            
        if line:
            # Parse progress
            match = time_regex.search(line)
            if match:
                try:
                    h, m, s = map(float, match.groups())
                    current_seconds = h * 3600 + m * 60 + s
                    
                    # Calculate percentage (Mapped from 40% to 95%)
                    # We reserve last 5% for finalization
                    percent_complete = min(1.0, current_seconds / total_duration)
                    global_progress = 40 + (percent_complete * 55) 
                    
                    if progress_callback:
                        progress_callback({
                            "status": "processing", 
                            "progress": min(99, global_progress), 
                            "message": f"Rendering... {int(percent_complete * 100)}%"
                        })
                except Exception as e:
                    # Catch cancellation from callback
                    print(f"🛑 Render Interrupted: {e}")
                    process.terminate()
                    process.wait()
                    raise e
                except: pass
        
        # Always check for cancellation even if no regex match
        # We ping with empty status check every loop? To avoid spam, maybe only every X lines?
        # But for responsiveness, checking often is fine as it's just a dict lookup in memory.
        try:
            if progress_callback:
                 # Sending just status check (pass empty dict to trigger callback logic without overwriting status)
                 progress_callback({})
        except Exception as e:
            print(f"🛑 Render Action Interrupted: {e}")
            process.terminate()
            process.wait()
            raise e


    # Check for success
    if process.returncode != 0:
        # We might have missed the error in the loop logic if we only looked for progress
        # Read whatever is left
        rem_err = process.stderr.read()
        print(f"FFmpeg Error:\n{rem_err}")
        raise Exception("FFmpeg Rendering Failed (Check server logs)")
    
    print(f"✅ Hybrid Render Complete: {output_path}")
    
    # Cleanup Temp
    # shutil.rmtree(TEMP_DIR) 

    if progress_callback:
        progress_callback({"status": "completed", "progress": 100, "message": "Render Complete", "url": f"/exports/{output_filename}"})

    return output_path


import os
import datetime

def format_timestamp(seconds):
    """
    Converts seconds (float) to SRT timestamp format: HH:MM:SS,mmm
    """
    td = datetime.timedelta(seconds=seconds)
    # Total seconds
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - total_seconds) * 1000)
    
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def generate_srt(project_data, output_path):
    """
    Generates a .srt subtitle file based on the FINAL timeline (Green clips only).
    Handles 'Time Shift' by calculating new cumulative timestamps.
    
    Args:
        project_data (dict): The full project JSON/EDL.
        output_path (str): Where to save the .srt file.
    """
    print(f"📝 Generating Subtitles -> {output_path}")
    
    clips_list = project_data.get('edl', project_data.get('clips', []))
    print(f"DEBUG: Found {len(clips_list)} clips for subtitles.")

    srt_content = ""
    subtitle_index = 1
    current_time = 0.0
    
    for clip in clips_list:
        # 1. Check if Clip is Kept (Green)
        keep_val = clip.get('keep', True)
        if isinstance(keep_val, str) and keep_val.lower() == 'false':
             keep_val = False
        
        # DEBUG
        text = clip.get('text', '').strip()
        print(f"DEBUG: Clip {clip.get('id')} - keep={keep_val}, text_len={len(text)}")

        if not keep_val:
            # print(f"Skipping Clip {clip.get('id')} (keep=False)")
            continue
        
        # print(f"Processing Clip {clip.get('id')} (metrics: {duration}s)")
            
        # 2. Get Text Content
        # text already fetched above for debug
        if not text:
            # Even if no text, we must advance time!
            # But we don't write an empty subtitle entry usually.
            pass
            
        # 3. Calculate Clip Duration (The "Math" of time shifting)
        try:
            start = float(clip.get('start', 0))
            end_val = clip.get('end')
            
            # Simple duration logic matching renderer
            if end_val and float(end_val) > 0:
                 duration = float(end_val) - start
            else:
                 duration = float(clip.get('duration', 0))
                 
            if duration <= 0: continue # Skip invalid clips
            
        except:
            continue
            
        # 4. Create SRT Entry (if text exists)
        if text:
            start_timestamp = format_timestamp(current_time)
            end_timestamp = format_timestamp(current_time + duration)
            
            srt_content += f"{subtitle_index}\n"
            srt_content += f"{start_timestamp} --> {end_timestamp}\n"
            srt_content += f"{text}\n\n"
            
            subtitle_index += 1
            
        # 5. Advance The "Master Clock"
        current_time += duration
        
    # Save File
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print("✅ SRT Generated Successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to write SRT: {e}")
        return False

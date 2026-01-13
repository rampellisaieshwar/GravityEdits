import os
import cv2
import numpy as np
import json
import requests
# Imports moved to functions to prevent startup locks
# from moviepy import VideoFileClip
# from faster_whisper import WhisperModel
# from deepface import DeepFace

# Settings
TEMP_AUDIO_DIR = "processing"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
MODEL_SIZE = "base"

def extract_audio(video_path):
    # Same as before
    base_name = os.path.basename(video_path)
    audio_path = os.path.join(TEMP_AUDIO_DIR, f"{base_name}.wav")
    if os.path.exists(audio_path): return audio_path
    
    from moviepy import VideoFileClip
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, logger=None)
    video.close()
    return audio_path

def transcribe_audio(audio_path):
    print(f"      [2/3] Transcribing Audio for {os.path.basename(audio_path)}...")
    
    import subprocess
    import sys
    
    try:
        process = subprocess.Popen(
            [sys.executable, "backend/audio_transcriber.py", audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error in transcription: {stderr}")
            # Fallback mock
            return [{
                "start": 0.0,
                "end": 5.0,
                "text": "[Transcription Failed]",
                "visual_data": {}
            }]

        # Parse the JSON output from the script
        # The script might print logs, but the last line should be the JSON
        lines = stdout.strip().split('\n')
        result_json_str = lines[-1] 
        return json.loads(result_json_str)
                
    except Exception as e:
        print(f"Failed to run isolated transcriber: {e}")
        return [{
            "start": 0.0,
            "end": 5.0,
            "text": "[System Failure]",
            "visual_data": {}
        }]

def analyze_visuals(video_path, clips):
    # Same as before
    # Prepare timestamps to analyze
    timestamps = []
    for clip in clips:
        timestamps.append((clip["start"], clip["end"]))
    
    import subprocess
    import sys
    
    # Run the isolated script
    # We pass the timestamps via stdin to the script
    try:
        process = subprocess.Popen(
            [sys.executable, "backend/visual_analyzer.py", video_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=json.dumps(timestamps))
        
        if process.returncode != 0:
            print(f"Error in visual analysis: {stderr}")
            # Fallback if it fails
            for clip in clips:
                clip["visual_data"] = {"brightness": "unknown", "emotion": "unknown"}
            return clips

        # Parse the JSON output from the script
        # The script prints some logs, but the last line should be the JSON
        lines = stdout.strip().split('\n')
        result_json_str = lines[-1] 
        results = json.loads(result_json_str)
        
        # Merge back
        for clip in clips:
            mid_point = (clip["start"] + clip["end"]) / 2
            key = str(mid_point)
            if key in results:
                clip["visual_data"] = results[key]
            else:
                clip["visual_data"] = {"brightness": "unknown", "emotion": "unknown"}
                
    except Exception as e:
        print(f"Failed to run isolated visual analyzer: {e}")
        for clip in clips:
             clip["visual_data"] = {"brightness": "unknown", "emotion": "unknown"}

    return clips

# --- NEW: THE BATCH PROCESSOR ---
def process_batch_pipeline(video_paths_list, project_name="Project_01", output_dir="uploads", progress_callback=None, user_description=None, api_key=None):
    """
    Takes a LIST of videos (e.g., ['intro.mp4', 'scene.mp4'])
    and combines them into ONE Master JSON.
    """
    print(f"🚀 Starting Batch Process for {len(video_paths_list)} videos...")
    if progress_callback: progress_callback(0, "Starting batch process...")
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    master_timeline = []
    global_id_counter = 1
    total_videos = len(video_paths_list)
    
    for i, video_path in enumerate(video_paths_list):
        base_progress = (i / total_videos) * 80
        progress_per_video = 80 / total_videos
        
        print(f"   ...Processing {os.path.basename(video_path)}")
        if progress_callback: progress_callback(base_progress + 5, f"Extracting Audio: {os.path.basename(video_path)}")
        
        # 1. Run our standard analysis
        print(f"      [1/3] Extracting Audio for {video_path}...")
        audio_path = extract_audio(video_path)
        
        if progress_callback: progress_callback(base_progress + (progress_per_video * 0.3), f"Transcribing: {os.path.basename(video_path)}")
        print(f"      [2/3] Transcribing Audio for {video_path}...")
        clips = transcribe_audio(audio_path)
        
        if progress_callback: progress_callback(base_progress + (progress_per_video * 0.6), f"Visual Analysis: {os.path.basename(video_path)}")
        print(f"      [3/3] Analyzing Visuals for {video_path}...")
        clips = analyze_visuals(video_path, clips)
        
        # 2. Tag them with the Source File (CRITICAL for editing later)
        for clip in clips:
            clip["id"] = global_id_counter  # Unique ID across ALL videos
            clip["source_video"] = os.path.basename(video_path) # Remember where it came from
            master_timeline.append(clip)
            global_id_counter += 1
            
    # 3. Save the Master JSON
    if progress_callback: progress_callback(85, "Saving analysis data...")
    project_data = {
        "project_name": project_name,
        "total_clips": len(master_timeline),
        "timeline": master_timeline
    }
    
    output_json_path = os.path.join(output_dir, f"{project_name}_analysis.json")
    with open(output_json_path, "w") as f:
        json.dump(project_data, f, indent=4)
        
    print(f"✅ BATCH COMPLETE! Master JSON saved to: {output_json_path}")
    
    # 4. Generate XML EDL for Frontend
    if progress_callback: progress_callback(90, "AI Generating Timeline (this may take a moment)...")
    output_xml_path = os.path.join(output_dir, f"{project_name}.xml")
    
    generate_xml_edl(project_data, output_xml_path, project_name, user_description, api_key=api_key)
    if progress_callback: progress_callback(100, "Done!")
    
    print(f"✅ XML EDL saved to: {output_xml_path}")
    
    return output_json_path

def generate_xml_edl(project_data, output_path, project_name="Project", user_description=None, api_key=None):
    print("🧠 Asking Llama 3 to edit the video...")
    
    # User instructions injection
    user_context = ""
    if user_description:
        user_context = f"""
        USER INSTRUCTIONS:
        The user has provided the following description/context for this edit.
        You MUST prioritize these instructions when selecting clips, style, and tone:
        "{user_description}"
        """

    # 1. Prepare Prompt
    # We strip some bulky data to keep context small if needed (but Llama 3 usually handles it)
    prompt = f"""
    You are a professional Video Editor AI. Your task is to create an EDL (Edit Decision List) in XML format based on the following analysis data of video clips.
    
    {user_context}

    CRITICAL RULES:
    1. Output ONLY valid XML. No markdown, no conversation.
    2. Review the 'visual_data' and 'text' (transcription).
    3. Keep clips that are visually 'bright' and have interesting speech.
    4. Reject clips (keep="false") that are 'dark' or have silence/boring text.
    5. The XML root must be <project name="{project_name}">. Inside, <edl> contains <clip> tags.
    6. YOU MUST INCLUDE ALL CLIPS from the input, even if you mark them as keep="false". Do not filter any clips out.
    7. Maintain the exact 'id', 'source', 'start', 'end' from input.
    8. CALCULATE DURATION: duration must be exactly (end - start). Do not output "..." or "unknown".
    9. You MUST include a 'reason' attribute for EVERY <clip> tag, explaining why it was kept or rejected.
    10. CRITICAL: You MUST include the 'text' attribute containing the transcription. Escape double quotes if needed.
    11. SUGGEST COLOR GRADING: For the project globally and for each clip, suggest color grading settings based on the mood.
       - brightness/exposure: -5.0 to 5.0 (default 0)
       - contrast: -100 to 100 (default 0)
    11. VIRAL SHORTS: Identification of 1-3 potential "Viral Shorts" from the footage.
       - Look for high-energy moments, funny bloopers, or strong hooks.
       - These should be separate from the main EDL.
       - Provide a 'title' and 'description' for the short.
       - List the 'clip_ids' that make up this short (comma separated).
    12. TEXT OVERLAYS: Analyze the ENTIRE transcript to understand the structure.
       - Generate text overlays ONLY for MAJOR TOPIC CHANGES or SECTION HEADERS.
       - Do NOT highlight random words. Only label the start of a new idea or chapter.
       - "content": The TOPIC TITLE or SECTION NAME (max 3 words). CRITICAL: Keep it short to fit on screen.
       - "start": Taking place exactly when the new topic begins.
       - "duration": 2.0 to 4.0 seconds.
       - "style": "pop" or "slide_up".
       - "origin": "ai".
       - "color": Hex code for text color (e.g., "#FF0000", "#FFFFFF", "#FFFF00"). Choose based on mood (e.g., Red for exciting/urgent, White for standard).
       - "size": Font size multiplier. STRICT RANGE: 2 to 6. Default 4. Never exceed 6 or it will be too big.
       - "x": Horizontal position percentage (10-90). Default 50 (center). STRICT: Do not use 0 or 100 to avoid cutting off.
       - "y": Vertical position percentage (10-90). Default 50 (center). STRICT: Do not use 0 or 100.
       - "font": Font family (e.g., "Impact", "Arial-Bold"). Use "Impact" for memes/excitement.
    OUTPUT SCHEMA:
    <project name="...">
      <global_settings>...</global_settings>
      <edl>...</edl>
      <viral_shorts>...</viral_shorts>
      <overlays>
        <text id="t1" content="INTRO" start="0.5" duration="2.0" style="pop" origin="ai" color="#FFFFFF" size="5" x="50" y="50" font="Impact"/>
        <text id="t2" content="KEY POINT" start="10.5" duration="3.0" style="slide_up" origin="ai" color="#FFFF00" size="4" x="50" y="80" font="Arial-Bold"/>
      </overlays>
    </project>

    INPUT DATA:
    {json.dumps(project_data, indent=2)}
    
    IMPORTANT: You MUST generate at least one <short> in the <viral_shorts> section if the footage allows.
    """
    
    # 2. Call Ollama (Llama 3) via Config
    try:
        from . import llm_config
    except ImportError:
        import llm_config
    
    try:
        if llm_config.LLM_PROVIDER == "ollama":
            url = f"{llm_config.OLLAMA_BASE_URL}/api/generate"
            payload = {
                "model": llm_config.LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.4  # Increased from 0.2 to allow some creativity for shorts
                }
            }
            
            response = requests.post(url, json=payload, timeout=180)
            
            if response.status_code == 200:
                result = response.json()
                llm_output = result.get("response", "").strip()
                
                # Simple cleanup to ensure we just get XML
                if "```xml" in llm_output:
                    llm_output = llm_output.split("```xml")[1].split("```")[0].strip()
                elif "```" in llm_output:
                    llm_output = llm_output.split("```")[1].split("```")[0].strip()
                    
                # Basic validation
                if "<project" in llm_output and "</project>" in llm_output:
                    with open(output_path, "w") as f:
                        f.write(llm_output)
                    print(f"✨ {llm_config.LLM_MODEL} generated an EDL!")
                    return
                else:
                    print(f"⚠️ {llm_config.LLM_MODEL} output invalid XML. Falling back to manual rule-based editing.")
            else:
                print(f"⚠️ Ollama Error: {response.status_code} - {response.text}")
        
        elif llm_config.LLM_PROVIDER == "gemini":
            try:
                import google.generativeai as genai
                
                # Determine Key (User > Config > None)
                key_to_use = api_key if api_key else llm_config.GEMINI_API_KEY
                
                if not key_to_use:
                    print("⚠️ No Gemini API Key provided. Cannot run AI analysis.")
                    raise Exception("Missing Gemini API Key")

                genai.configure(api_key=key_to_use)
                
                model = genai.GenerativeModel(
                    llm_config.LLM_MODEL,
                    generation_config=genai.GenerationConfig(
                        temperature=0.4,
                    )
                )
                
                # ... same generation logic ...
                response = model.generate_content(prompt)
                llm_output = response.text.strip()
                
                # Simple cleanup
                if "```xml" in llm_output:
                    llm_output = llm_output.split("```xml")[1].split("```")[0].strip()
                elif "```" in llm_output:
                    llm_output = llm_output.split("```")[1].split("```")[0].strip()
                
                if "<project" in llm_output and "</project>" in llm_output:
                    with open(output_path, "w") as f:
                        f.write(llm_output)
                    print(f"✨ {llm_config.LLM_MODEL} generated an EDL!")
                    return
                else:
                    print(f"⚠️ {llm_config.LLM_MODEL} output invalid XML: {llm_output[:100]}...")
            
            except Exception as e:
                print(f"⚠️ Gemini Error: {e}")
        
        else:
             print(f"Provider {llm_config.LLM_PROVIDER} not implemented.")

    except Exception as e:
        print(f"⚠️ Failed to connect to AI: {e}. Falling back to manual logic.")

    # 3. Fallback Manual Logic (if LLM fails)
    print("⚙️ Running manual fallback logic...")
    edl_content = f'<project name="{project_name}">\n'
    edl_content += '  <global_settings>\n    <filter_suggestion>Natural Grade</filter_suggestion>\n'
    edl_content += '    <color_grading>\n      <temperature>5600</temperature>\n      <exposure>0</exposure>\n      <contrast>0</contrast>\n      <saturation>100</saturation>\n      <filter_strength>100</filter_strength>\n    </color_grading>\n  </global_settings>\n'
    edl_content += '  <edl>\n'
    
    for clip in project_data.get("timeline", []):
        keep = "true"
        reason = "Manual Fallback"
        visuals = clip.get("visual_data", {})
        
        if visuals.get("brightness") == "dark":
             keep = "false"
             reason = "Too dark (Manual)"
             
        escaped_text = clip.get("text", "").replace('"', "'")
        edl_content += f'    <clip id="{clip.get("id")}" source="{clip.get("source_video")}" start="{clip.get("start")}" end="{clip.get("end")}" keep="{keep}" reason="{reason}" text="{escaped_text}" duration="{clip.get("end") - clip.get("start")}">\n'
        edl_content += '      <color_grading>\n        <temperature>5600</temperature>\n        <exposure>0</exposure>\n        <contrast>0</contrast>\n        <saturation>100</saturation>\n        <filter_strength>100</filter_strength>\n      </color_grading>\n'
        edl_content += '    </clip>\n'
        
    edl_content += '  </edl>\n  <viral_shorts>\n  </viral_shorts>\n  <overlays>\n  </overlays>\n</project>'
    
    with open(output_path, "w") as f:
        f.write(edl_content)

# --- TEST AREA ---
if __name__ == "__main__":
    # Test with a list of videos
    # Make sure you have these files or change the names!
    test_files = ["uploads/WTN1.mp4","uploads/WTN2.mp4","uploads/WTN3.mp4"] 
    
    # You can add more: test_files = ["uploads/intro.mp4", "uploads/main.mp4"]
    
    if os.path.exists(test_files[0]):
        process_batch_pipeline(test_files, "Test_Project")
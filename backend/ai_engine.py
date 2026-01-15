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

    try:
        from . import llm_config
        key = api_key if api_key else llm_config.GEMINI_API_KEY
        
        # Configure Gemini (New SDK)
        import google.generativeai as genai
        genai.configure(api_key=key)
        
        # Convert JSON to string
        json_input = json.dumps(project_data, indent=2)
        
        # Use user_description if provided, otherwise a default
        user_desc = user_description if user_description else 'Make it viral and fast-paced.'

        prompt = f"""
        ROLE: Expert Video Editor, Linguist, and Colorist.
        
        INPUT DATA (Sanitized but may still contain errors):
        {json_input}
        
        USER CONTEXT: "{user_desc}"
        
        ---------------------------------------------------------
        YOUR 5-STEP MISSION (THE "WAKULLAH" PROTOCOL):
        ---------------------------------------------------------
        
        STEP 1: TEXT SANITIZATION (The Ghostbuster Filter)
        - The transcript may still contain phantom words (e.g., "Banana", "Penguin", "Steam").
        - RULE: If a word is a random noun that doesn't fit the sentence context, DELETE IT.
        - RULE: Fix phonetic errors (e.g., "Pre-ill" -> "Premiere", "Strain moral" -> "Train models").
        - OUTPUT: Use this CLEANED text in the final XML.
        
        STEP 2: SURGICAL EDITING (Bad Takes & Quality Control)
        - Look for semantic duplicates (e.g., "The first step... [pause]... The first step is...").
        - ACTION: Keep ONLY the best/last version. Mark the others as keep="false".
        - RULE: Cut "dead air" by adjusting 'start' and 'end' times to match the clean speech.
        - CRITICAL RULE (QUALITY CONTROL):
          - If a clip contains broken grammar, stuttering that breaks flow, or nonsense words, SET keep="false" reason="Bad Grammar/Flow".
          - If a clip is just laughing, breathing, coughing, or silence with no meaningful speech, SET keep="false" reason="Non-verbal/Noise".
          - If the transcript is unintelligible or hallucinated (random words), SET keep="false" reason="Bad Audio/Transcript".
        
        STEP 3: VISUAL REPAIR (The "Fix It" Logic)
        - Check 'visual_data' for each clip.
        - IF brightness is "dark" or "low":
          - DO NOT DELETE. Instead, ADD: <correction type="brightness" value="1.4" />
        - IF emotion is "dull":
          - ADD: <correction type="saturation" value="1.2" />
          
        STEP 4: VIRAL ENHANCEMENTS (Overlays)
        - Identify 3-5 "High Value" moments (Topic shifts, Punchlines).
        - GENERATE <overlays> for them.
        - Style: "pop", "slide_up" | "typewriter".
        - Colors: Yellow (#FFFF00) for emphasis, White (#FFFFFF) for standard.
        
        STEP 5: VIRAL SHORTS (The Hook)
        - YOU MUST Identify at least 2 separate sequences (15s-60s) that act as standalone viral shorts.
        - Even if the footage is boring, find the best contiguous segments (e.g., a funny mistake or the most energetic part).
        - Add them to the <viral_shorts> section.
        - Ensure 'clip_ids' corresponds to the 'id' attributes of the clips you kept in the EDL.
        
        ---------------------------------------------------------
        OUTPUT FORMAT (Strict XML):
        ---------------------------------------------------------
        <project name="{project_name}">
            <global_settings>
                <frame_rate>30</frame_rate>
            </global_settings>
            
            <edl>
                <clip id="1" source="video.mp4" start="0.5" end="4.2" keep="true" reason="Clean intro" text="Welcome to the AI editor">
                    <correction type="brightness" value="1.3" /> 
                </clip>
                
                <clip id="2" source="video.mp4" start="4.2" end="8.0" keep="false" reason="Redundant / Bad Audio" />
            </edl>
            
            <viral_shorts>
                <short>
                    <title>The Secret Trick</title>
                    <clip_ids>5,6,7</clip_ids>
                </short>
            </viral_shorts>
            
            <overlays>
                <text id="t1" content="GAME CHANGER" start="0.5" duration="2.0" style="pop" color="#FFFF00" size="5" x="50" y="50" font="Arial-Bold"/>
            </overlays>
        </project>
        """
        
        # Call Gemini (Standard SDK)
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)
        
        # Clean Output
        # Handle potential safety block or empty response
        if not response.text:
             print("AI returned empty response (Safety Block?)")
             raise ValueError("AI Safety Block")

        xml_out = response.text.replace("```xml", "").replace("```", "").strip()
        
        with open(output_path, "w") as f:
            f.write(xml_out)
            
        print(f"✨ Master EDL Generated with Wakullah Protocol!")
        return True
            
    except Exception as e:
        print(f"❌ AI Generation Failed: {e}")
        # Fallback dump for manual review
        with open(output_path, "w") as f:
            f.write(f"<project name='{project_name}'><error>AI Failed: {str(e)}</error></project>")

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
        
    edl_content += '  </edl>\n'
    
    # Generate a fallback Viral Short using the first few kept clips
    kept_ids = [str(c.get("id")) for c in project_data.get("timeline", []) if c.get("visual_data", {}).get("brightness") != "dark"][:3]
    kept_ids_str = ",".join(kept_ids) if kept_ids else "1,2,3"
    
    edl_content += f'''  <viral_shorts>
    <short>
      <title>Best Moments (Fallback)</title>
      <clip_ids>{kept_ids_str}</clip_ids>
    </short>
  </viral_shorts>
'''
    edl_content += '  <overlays>\n  </overlays>\n</project>'
    
    with open(output_path, "w") as f:
        f.write(edl_content)
        
    return False

# --- TEST AREA ---
if __name__ == "__main__":
    # Test with a list of videos
    # Make sure you have these files or change the names!
    test_files = ["uploads/WTN1.mp4","uploads/WTN2.mp4","uploads/WTN3.mp4"] 
    
    # You can add more: test_files = ["uploads/intro.mp4", "uploads/main.mp4"]
    
    if os.path.exists(test_files[0]):
        process_batch_pipeline(test_files, "Test_Project")
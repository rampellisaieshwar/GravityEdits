import os
import json
import requests
# Imports moved to functions to prevent startup locks
# from moviepy import VideoFileClip
# from faster_whisper import WhisperModel
# from deepface import DeepFace
# import cv2
# import numpy as np

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

# --- GEMINI API HELPER ---
def call_gemini_api(prompt, key, model="gemini-2.0-flash"):
    """
    Standalone helper to call Gemini REST API.
    """
    import requests
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code != 200:
            print(f"Gemini API Error {resp.status_code}: {resp.text}")
            return None
        
        result = resp.json()
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except:
            print(f"Unexpected response structure: {result}")
            return None
    except Exception as e:
        print(f"REST Request failed: {e}")
        return None

def generate_xml_edl(project_data, output_path, project_name="Project", user_description=None, api_key=None):
    print("🧠 Starting Two-Stage AI Editing Process (Inspector -> Director)...")
    
    if not api_key:
         from . import llm_config
         api_key = llm_config.GEMINI_API_KEY
         
    if not api_key:
         print("❌ Missing API Key for Gemini. Switching to Manual Fallback.")
         return perform_manual_fallback(project_data, output_path, project_name)

    # Convert JSON to string for AI
    json_input = json.dumps(project_data, indent=2)
    user_desc = user_description if user_description else 'Make it viral and fast-paced.'
    target_audience = "General Social Media Audience"

    # --- STAGE 1: THE INSPECTOR ---
    print("🕵️ Stage 1: The Inspector (Analyzing content for errors...)")
    inspector_report = "[]"
    
    try:
        inspector_prompt = f"""
ROLE: Forensic Transcription Analyst & Quality Control Agent.
TASK: Analyze the following video timeline JSON and identify specific errors.
INPUT DATA: {json_input}

YOUR MISSION:
1. Detect "Ghost Words": Words that don't fit the context (e.g., "Banana", "Penguin", "Steam") appearing in random sentences.
2. Detect "Hallucinations": Gibberish text generated by the transcriber (e.g., "Thank you. Bye.", "Amara...").
3. Detect "Bad Takes": Incomplete sentences, stuttering loops, or unintelligible speech.
4. Detect "Non-Verbal": Laughing, coughing, or heavy breathing labeled as text.

OUTPUT FORMAT:
Strictly return a JSON LIST of objects. Do not write markdown.
[
  {{ "id": 1, "type": "ghost_word", "reason": "Random noun 'Banana' in tech talk", "confidence": "high" }},
  {{ "id": 5, "type": "bad_take", "reason": "Stuttering loop", "confidence": "high" }}
]

If no errors are found, return '[]'.
"""
        response_1 = call_gemini_api(inspector_prompt, api_key)
        if response_1:
            # Clean comments
            clean_resp = response_1.replace("```json", "").replace("```", "").strip()
            inspector_report = clean_resp
            print(f"   📋 Inspector Report: {inspector_report[:100]}...")
        else:
            print("   ⚠️ Inspector detection skipped (API error), proceeding blindly.")
            
    except Exception as e:
         print(f"   ⚠️ Inspector failed: {e}")

    # --- STAGE 2: THE DIRECTOR ---
    print("🎬 Stage 2: The Director (Generating XML EDL...)")
    
    director_prompt = f"""
ROLE: Expert Video Editor (AI), Viral Content Strategist, and Motion Graphics Supervisor.

INPUT DATA: {json_input}
INSPECTOR REPORT (ERRORS): {inspector_report}
USER CONTEXT: "{user_desc}"
TARGET AUDIENCE: "{target_audience}"

---------------------------------------------------------
YOUR 6-STEP MISSION (THE "SUPER-WAKULLAH V2" PROTOCOL):
---------------------------------------------------------

STEP 1: CONTEXTUAL SANITIZATION (Using Inspector Report)
- Use the INSPECTOR REPORT to verify clips. 
- If the Inspector flagged a clip as "ghost_word" or "hallucination", you MUST set keep="false" reason="Hallucination".
- Remove "Ghost Words" and fix phonetic errors only if confidence > 90%.

STEP 2: SURGICAL EDITING & PACING
- Remove semantic duplicates (keep the best take).
- Calculate silence duration. If > 0.8s, mark as "jump_cut_needed".
- Set keep="false" for incomplete sentences or severe stuttering.

STEP 3: VISUAL & AUDIO REPAIR
- Brightness: If "dark", add <correction type="brightness" value="1.3" />.
- Audio: If "quiet", add <correction type="gain" value="+5db" />.
- Saturation: If "dull", add <correction type="saturation" value="1.2" />.

STEP 4: MANDATORY OVERLAY GENERATION (ZERO TOLERANCE)
- **CRITICAL RULE:** You CANNOT output an empty overlay list.
- **TIMING ACCURACY:** You MUST use the exact `start` and `end` timestamps from the INPUT DATA JSON for the corresponding spoken words. Do NOT guess the time. If the overlay highlights a word, use that word's exact timestamp from the source JSON.
- **The Hook:** You MUST generate a "pop" style overlay for the very first 3 seconds of the video.
- **Keywords:** Identify at least 3 "Power Nouns" (e.g., "Money", "Secret", "AI") and generate a "highlight" overlay for them.
- **Pacing:** Ensure there is at least one visual overlay element every 10 seconds to maintain retention.

STEP 5: COMPULSORY VIRAL SHORTS (THE "NO EXCUSES" RULE)
- **CRITICAL RULE:** You MUST extract exactly 3 distinct sequences (15s - 60s) suitable for TikTok/Reels.
- **Logic:** Even if the video is slow, you must find the "Best Available" contiguous segments based on:
  1. Loudest audio (High energy).
  2. Fastest speech rate (Pacing).
  3. Topic changes (New information).
- Add these to the <viral_shorts> section with a "Viral Score" (1-100).

STEP 6: PRIORITY SCORING
- Assign a PRIORITY SCORE (1-5) to every clip in the EDL.
- 5 = Essential/Hook (Must Keep).
- 1 = Tangent/Filler (First to Cut).
 - ****MANDATORY:**** You MUST include the `source` attribute in every <clip> tag, copying the `source_video` value from the input JSON exactly.

---------------------------------------------------------
OUTPUT FORMAT (Strict XML):
---------------------------------------------------------
<project name="{project_name}">
    <global_settings>
        <aspect_ratio>9:16</aspect_ratio>
    </global_settings>

    <edl>
        <clip id="1" source="video.mp4" start="0.0" end="4.0" keep="true" priority="5" text="This is the only way to fix it.">
             <correction type="brightness" value="1.2" />
        </clip>
    </edl>

    <viral_shorts>
        <short id="s1" duration="45s" viral_score="92">
            <title>The Main Hook</title>
            <reason>High energy intro + controversial statement</reason>
            <clip_ids>1,2,3</clip_ids>
        </short>
    </viral_shorts>

    <overlays>
        <text content="STOP SCROLLING" start="0.0" duration="1.5" style="impact_pop" color="#FF0000" size="large" />
    </overlays>

</project>
"""
    try:
        response_text = call_gemini_api(director_prompt, api_key)
        
        if not response_text:
             print("AI returned empty or error.")
             raise Exception("AI API returned empty or failed to generate response.")

        xml_out = response_text.replace("```xml", "").replace("```", "").strip()
        
        with open(output_path, "w") as f:
            f.write(xml_out)
            
        print(f"✨ Master EDL Generated with Wakullah Protocol!")
        return True
            
    except Exception as e:
        print(f"❌ AI Generation Failed: {e}")
        # Fallback dump for manual review
        with open(output_path, "w") as f:
            f.write(f"<project name='{project_name}'><error>AI Failed: {str(e)}</error></project>")
        return perform_manual_fallback(project_data, output_path, project_name)

def perform_manual_fallback(project_data, output_path, project_name):
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
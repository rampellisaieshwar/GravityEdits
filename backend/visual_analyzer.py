
import sys
import json
import cv2
import numpy as np

# Lazy load DeepFace only when this script runs
# from deepface import DeepFace

def analyze_video(video_path):
    print(f"Analyzing {video_path}...", file=sys.stderr)
    cap = cv2.VideoCapture(video_path)
    
    # We will just analyze a few frames to be fast/safe
    # For now, let's just do what the original code did: analyze specific timestamps?
    # Actually checking the original code, it passed "clips" and analyzed the midpoint of those clips.
    # To keep this script simple and stateless, we will accept a list of timestamps to analyze from stdin.
    
    input_data = sys.stdin.read()
    if not input_data:
        return {}
        
    timestamps = json.loads(input_data) # Expecting a list of float timestamps (seconds)
    results = {}
    
    for start, end in timestamps:
        mid_point = (start + end) / 2
        cap.set(cv2.CAP_PROP_POS_MSEC, mid_point * 1000)
        ret, frame = cap.read()
        
        if not ret:
            results[str(mid_point)] = {"brightness": "unknown", "emotion": "unknown"}
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        brightness_val = "bright" if brightness > 50 else "dark"
        
        emotion = "neutral"
        # try:
        #     analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, silent=True)
        #     emotion = analysis[0]['dominant_emotion']
        # except:
        #     pass
            
        results[str(mid_point)] = {
            "brightness": brightness_val,
            "blur_score": cv2.Laplacian(gray, cv2.CV_64F).var(), # Laplacian Variance
            "saturation_avg": np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)[:, :, 1]), # HSV Saturation
            "emotion": emotion 
        }
        
    cap.release()
    print(json.dumps(results))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visual_analyzer.py <video_path>", file=sys.stderr)
        sys.exit(1)
        
    video_path = sys.argv[1]
    analyze_video(video_path)


import sys
import json
import os

def transcribe_audio_file(audio_path):
    print(f"Loading Whisper Model for {audio_path}...", file=sys.stderr)
    try:
        import whisper
        import warnings
        
        # Suppress FP16 warning on CPU
        warnings.filterwarnings("ignore")
        
        model_size = os.getenv("WHISPER_MODEL", "tiny.en")
        
        # Load model (standard OpenAI Whisper)
        model = whisper.load_model(model_size)
        
        # Transcribe
        result = model.transcribe(audio_path, word_timestamps=True)
        
        clips = []
        for s in result.get("segments", []):
            clip_words = []
            if "words" in s:
                for w in s["words"]:
                    # OpenAI Whisper structure: {word, start, end, probability}
                    prob = w.get("probability", 1.0)
                    if prob >= 0.20:
                        clip_words.append({
                            "word": w.get("word", "").strip(),
                            "start": round(w.get("start"), 2),
                            "end": round(w.get("end"), 2),
                            "probability": round(prob, 2)
                        })
            
            # Rebuild text
            clean_text = " ".join([w["word"] for w in clip_words])
            final_text = clean_text if clean_text.strip() else s.get("text", "").strip()
            
            clips.append({
                "start": round(s.get("start"), 2),
                "end": round(s.get("end"), 2),
                "text": final_text,
                "words": clip_words,
                "visual_data": {} 
            })
            
        print(json.dumps(clips))
        
    except Exception as e:
        print(f"Transcription Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_transcriber.py <audio_path>", file=sys.stderr)
        sys.exit(1)
        
    audio_path = sys.argv[1]
    transcribe_audio_file(audio_path)

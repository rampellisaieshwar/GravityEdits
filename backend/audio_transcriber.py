
import sys
import json
import os

def transcribe_audio_file(audio_path):
    print(f"Loading Whisper Model for {audio_path}...", file=sys.stderr)
    try:
        from faster_whisper import WhisperModel
        model_size = os.getenv("WHISPER_MODEL", "tiny.en")
        
        # Run on CPU with int8 to save memory/compatibility
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        segments, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)
        
        clips = []
        for s in segments:
            clip_words = []
            if s.words:
                for w in s.words:
                    if w.probability >= 0.20:  # Relaxed Filter: Only delete absolute noise
                        clip_words.append({
                            "word": w.word.strip(),
                            "start": round(w.start, 2),
                            "end": round(w.end, 2),
                            "probability": round(w.probability, 2)
                        })

            # Rebuild text from verified words only
            clean_text = " ".join([w["word"] for w in clip_words])
            
            # Fallback: If heavy filtering removed everything, keep original text to avoid "[Transcription Failed]"
            final_text = clean_text if clean_text.strip() else s.text.strip()

            clips.append({
                "start": round(s.start, 2),
                "end": round(s.end, 2),
                "text": final_text,
                "words": clip_words, # Might be empty if confidence low, AI must handle this
                "visual_data": {} 
            })
            
        print(json.dumps(clips))
        
    except Exception as e:
        print(f"Transcription Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_transcriber.py <audio_path>", file=sys.stderr)
        sys.exit(1)
        
    audio_path = sys.argv[1]
    transcribe_audio_file(audio_path)

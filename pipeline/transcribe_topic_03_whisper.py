import os
import sys
import json
import time
from pathlib import Path
import whisper
import torch

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    audio_path = r"C:\Users\Indresh HL\Downloads\TOPIC_03_FULL_VOICEOVER.mp3"
    output_json = Path(r"production/topic_03/audio/full_timeline_word_timestamps.json")
    output_json.parent.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Loading Whisper model ('base.en') on {device}...")
    t0 = time.time()
    model = whisper.load_model("base.en", device=device)
    print(f"[*] Model loaded in {time.time() - t0:.2f}s")

    print(f"[*] Transcribing master audio: {audio_path}...")
    t1 = time.time()
    result = model.transcribe(audio_path, word_timestamps=True, verbose=False)
    print(f"[*] Transcription finished in {time.time() - t1:.2f}s")

    total_words = 0
    segments = []
    for s in result.get("segments", []):
        words = []
        for w in s.get("words", []):
            words.append({
                "word": w["word"].strip(),
                "start": round(w["start"], 3),
                "end": round(w["end"], 3)
            })
            total_words += 1
        segments.append({
            "id": s["id"],
            "start": round(s["start"], 3),
            "end": round(s["end"], 3),
            "text": s["text"].strip(),
            "words": words
        })

    output_data = {
        "audio_file": audio_path,
        "total_words": total_words,
        "total_segments": len(segments),
        "segments": segments
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Saved {len(segments)} segments ({total_words} words) to {output_json}!")

if __name__ == "__main__":
    main()

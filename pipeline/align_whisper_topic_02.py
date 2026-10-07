import whisper
import json
import time
import os

print("[+] Loading Whisper model on CUDA GPU...")
t0 = time.time()
model = whisper.load_model("base", device="cuda")

audio_file = "production/topic_02/audio/final_timeline_audio.aac"
print(f"[+] Transcribing {audio_file} with word-level timestamps on GPU...")
result = model.transcribe(audio_file, word_timestamps=True, verbose=False)

words = []
segments = []

for seg in result["segments"]:
    seg_info = {
        "id": seg["id"],
        "start": round(seg["start"], 3),
        "end": round(seg["end"], 3),
        "text": seg["text"].strip(),
        "words": []
    }
    for w in seg.get("words", []):
        w_data = {
            "word": w["word"].strip(),
            "start": round(w["start"], 3),
            "end": round(w["end"], 3)
        }
        words.append(w_data)
        seg_info["words"].append(w_data)
        
    segments.append(seg_info)

output_data = {
    "duration": round(result["segments"][-1]["end"], 2) if result["segments"] else 0,
    "total_words": len(words),
    "segments": segments,
    "all_words": words
}

out_file = "production/topic_02/audio/full_timeline_word_timestamps.json"
os.makedirs("production/topic_02/audio", exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"[SUCCESS] Transcribed {len(words)} words across {len(segments)} segments in {time.time() - t0:.1f}s!")
print(f"[SUCCESS] Saved to {out_file}")

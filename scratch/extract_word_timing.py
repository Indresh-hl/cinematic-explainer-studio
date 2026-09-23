import whisper
import json

print("Loading Whisper base model...")
model = whisper.load_model("base")
print("Transcribing assets/audio_test_line13.mp3 with word_timestamps...")
result = model.transcribe("assets/audio_test_line13.mp3", word_timestamps=True)

words_data = []
for seg in result["segments"]:
    print(f"Segment: {seg['text']}")
    for w in seg["words"]:
        print(f"  {w['start']:0.2f}s - {w['end']:0.2f}s: '{w['word']}'")
        words_data.append({
            "word": w["word"].strip(),
            "start": round(w["start"], 3),
            "end": round(w["end"], 3)
        })

with open("assets/line13_word_timestamps.json", "w") as f:
    json.dump(words_data, f, indent=2)

print("Saved assets/line13_word_timestamps.json successfully!")

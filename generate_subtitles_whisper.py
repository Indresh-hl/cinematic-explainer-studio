import os
import whisper

video_path = r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\0922 (1).mp4"
srt_output_1 = r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\0922 (1).srt"
srt_output_2 = r"c:\Users\Indresh HL\Downloads\youtube long fromat\captions.srt"

print("Loading Whisper base model on CUDA...")
model = whisper.load_model("base", device="cuda")

print(f"Transcribing audio from: {video_path}")
# word_timestamps=True allows finer subtitle chunking
result = model.transcribe(video_path, language="en", verbose=False, word_timestamps=True)

def format_timestamp(seconds):
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        seconds += 1
        millis = 0
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

# Build snappy, well-spaced subtitle lines (max 6-8 words per line for modern video style)
subtitles = []
sub_index = 1

for seg in result["segments"]:
    words = seg.get("words", [])
    if not words:
        start_ts = format_timestamp(seg["start"])
        end_ts = format_timestamp(seg["end"])
        text = seg["text"].strip()
        if text:
            subtitles.append((sub_index, start_ts, end_ts, text))
            sub_index += 1
        continue

    chunk = []
    chunk_start = None
    for w in words:
        if chunk_start is None:
            chunk_start = w["start"]
        chunk.append(w["word"])
        
        # Split after 6 words, or on punctuation (. , ! ?), or pause > 0.5s
        is_punct = w["word"].rstrip().endswith((".", "!", "?", ";"))
        is_comma = w["word"].rstrip().endswith(",")
        if len(chunk) >= 6 or (len(chunk) >= 4 and is_comma) or is_punct:
            chunk_end = w["end"]
            text = " ".join(chunk).strip()
            if text:
                subtitles.append((sub_index, format_timestamp(chunk_start), format_timestamp(chunk_end), text))
                sub_index += 1
            chunk = []
            chunk_start = None

    if chunk and chunk_start is not None:
        chunk_end = words[-1]["end"]
        text = " ".join(chunk).strip()
        if text:
            subtitles.append((sub_index, format_timestamp(chunk_start), format_timestamp(chunk_end), text))
            sub_index += 1

srt_content = ""
for idx, start, end, text in subtitles:
    srt_content += f"{idx}\n{start} --> {end}\n{text}\n\n"

for out_path in [srt_output_1, srt_output_2]:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"Saved SRT to: {out_path}")

print(f"Total subtitles generated: {len(subtitles)}")

import asyncio
import os
import re
import subprocess
import edge_tts

# Audio settings
VOICE = "en-US-ChristopherNeural"
RATE = "-3%"
PITCH = "+3Hz"  # User requested: a little higher pitch than the standard -2Hz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(BASE_DIR)
AUDIO_DIR = os.path.join(WORKSPACE_DIR, "production", "topic_02", "audio")
TEMP_DIR = os.path.join(AUDIO_DIR, "temp_chunks")
TELEPROMPTER_FILE = os.path.join(BASE_DIR, "topic_02_teleprompter.txt")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def parse_pause_duration(pause_text):
    match = re.search(r'([\d\.]+)s', pause_text)
    if match:
        return float(match.group(1))
    return 1.2

def create_silence(duration_sec, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec),
        "-acodec", "libmp3lame",
        "-b:a", "64k",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def get_audio_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(result.stdout.strip())

async def generate_speech_chunk(text, output_mp3):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    word_boundaries = []
    with open(output_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append(chunk)
    return word_boundaries

def format_timestamp_srt(seconds):
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    mins = seconds // 60
    hours = mins // 60
    mins = mins % 60
    secs = seconds % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

async def main():
    print(f"Reading teleprompter script from: {TELEPROMPTER_FILE}")
    with open(TELEPROMPTER_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("====================================================================")
    body = parts[-1].strip()

    tokens = re.split(r'(\[PAUSE\s+[\d\.]+s(?:\s+COUNTDOWN)?\])', body)
    
    file_list = []
    chunk_index = 0
    cumulative_time = 0.0
    timeline_markers = []
    all_word_boundaries = []
    
    print(f"Generating voiceover using voice: {VOICE} (Pitch: {PITCH}, Rate: {RATE})...\n")
    
    for item in tokens:
        item = item.strip()
        if not item:
            continue
            
        if item.startswith("[PAUSE"):
            dur = parse_pause_duration(item)
            silence_file = os.path.join(TEMP_DIR, f"pause_{chunk_index:03d}_{dur}s.mp3")
            create_silence(dur, silence_file)
            file_list.append(silence_file)
            timeline_markers.append({
                "type": "pause",
                "duration": dur,
                "start": cumulative_time,
                "end": cumulative_time + dur,
                "label": item
            })
            cumulative_time += dur
            chunk_index += 1
        else:
            speech_file = os.path.join(TEMP_DIR, f"speech_{chunk_index:03d}.mp3")
            word_count = len(item.split())
            print(f"[{chunk_index:02d}] Generating chunk ({word_count} words): \"{item[:45]}...\"")
            wb = await generate_speech_chunk(item, speech_file)
            dur = get_audio_duration(speech_file)
            file_list.append(speech_file)
            timeline_markers.append({
                "type": "speech",
                "duration": dur,
                "start": cumulative_time,
                "end": cumulative_time + dur,
                "text": item
            })
            
            # Record word boundaries offset
            for entry in wb:
                # offset in 100ns units -> seconds
                w_start = entry["offset"] / 10000000.0 + cumulative_time
                w_dur = entry["duration"] / 10000000.0
                all_word_boundaries.append({
                    "word": entry["text"],
                    "start": round(w_start, 3),
                    "end": round(w_start + w_dur, 3)
                })
                
            cumulative_time += dur
            chunk_index += 1

    print(f"\nAll {len(file_list)} chunks created! Estimated total duration: {cumulative_time:.2f}s ({cumulative_time/60:.2f} min)")

    # Concatenate all into full master audio
    concat_list_file = os.path.join(TEMP_DIR, "concat_list.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for fpath in file_list:
            clean_path = fpath.replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    master_audio_path = os.path.join(AUDIO_DIR, "full_voiceover_master.mp3")
    print(f"\nConcatenating master audio to: {master_audio_path} ...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        master_audio_path
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    master_duration = get_audio_duration(master_audio_path)
    mins = int(master_duration // 60)
    secs = int(master_duration % 60)
    print(f"Master voiceover generated successfully! Final duration: {master_duration:.2f}s ({mins}m {secs}s)")

    # Split into Act audio files
    act_definitions = [
        {"act": 1, "end_phrase": "doomed to fail."},
        {"act": 2, "end_phrase": "ran out of glucose."},
        {"act": 3, "end_phrase": "biological turning point."},
        {"act": 4, "end_phrase": "actively happening."},
        {"act": 5, "end_phrase": "reset your brain focus."}
    ]

    current_act_idx = 0
    current_act_files = []

    print("\nExtracting Act-specific voiceover files...")
    for i, marker in enumerate(timeline_markers):
        current_act_files.append(file_list[i])
        if marker["type"] == "speech" and current_act_idx < len(act_definitions):
            target_phrase = act_definitions[current_act_idx]["end_phrase"]
            if target_phrase in marker.get("text", ""):
                act_num = act_definitions[current_act_idx]["act"]
                act_output = os.path.join(AUDIO_DIR, f"act{act_num}_voiceover.mp3")
                act_concat_txt = os.path.join(TEMP_DIR, f"act{act_num}_concat.txt")
                with open(act_concat_txt, "w", encoding="utf-8") as af:
                    for cf in current_act_files:
                        af.write(f"file '{cf.replace('\\', '/')}'\n")
                subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", act_concat_txt, "-c", "copy", act_output
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                act_dur = get_audio_duration(act_output)
                print(f"  -> Act {act_num} Voiceover: {act_output} ({act_dur:.1f}s)")
                current_act_idx += 1
                current_act_files = []

    if current_act_files and current_act_idx < len(act_definitions):
        act_num = 5
        act_output = os.path.join(AUDIO_DIR, f"act{act_num}_voiceover.mp3")
        act_concat_txt = os.path.join(TEMP_DIR, f"act{act_num}_concat.txt")
        with open(act_concat_txt, "w", encoding="utf-8") as af:
            for cf in current_act_files:
                af.write(f"file '{cf.replace('\\', '/')}'\n")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", act_concat_txt, "-c", "copy", act_output
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        act_dur = get_audio_duration(act_output)
        print(f"  -> Act {act_num} Voiceover: {act_output} ({act_dur:.1f}s)")

    # Save word timestamps json
    import json
    timestamps_json_path = os.path.join(AUDIO_DIR, "word_timestamps.json")
    with open(timestamps_json_path, "w", encoding="utf-8") as jf:
        json.dump(all_word_boundaries, jf, indent=2)
    print(f"\nWord timestamps saved: {timestamps_json_path} ({len(all_word_boundaries)} words)")

    # Generate basic SRT
    srt_path = os.path.join(AUDIO_DIR, "full_voiceover.srt")
    with open(srt_path, "w", encoding="utf-8") as sf:
        sub_idx = 1
        for marker in timeline_markers:
            if marker["type"] == "speech":
                sf.write(f"{sub_idx}\n")
                sf.write(f"{format_timestamp_srt(marker['start'])} --> {format_timestamp_srt(marker['end'])}\n")
                sf.write(f"{marker['text']}\n\n")
                sub_idx += 1
    print(f"Subtitles generated: {srt_path}")

    # Also copy or mirror into script/audio/topic_02 for backward compatibility
    import shutil
    legacy_audio_dir = os.path.join(BASE_DIR, "audio", "topic_02")
    os.makedirs(legacy_audio_dir, exist_ok=True)
    shutil.copy2(master_audio_path, os.path.join(legacy_audio_dir, "full_voiceover_master.mp3"))
    print(f"Mirror copied to: {legacy_audio_dir}/full_voiceover_master.mp3")

if __name__ == "__main__":
    asyncio.run(main())

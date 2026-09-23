import asyncio
import os
import re
import subprocess
import edge_tts

VOICE = "en-US-ChristopherNeural"
RATE = "-3%"
PITCH = "-2Hz"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
TEMP_DIR = os.path.join(AUDIO_DIR, "temp_chunks")
TELEPROMPTER_FILE = os.path.join(BASE_DIR, "teleprompter_clean.txt")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def parse_pause_duration(pause_text):
    # e.g., [PAUSE 1.5s] or [PAUSE 5.0s COUNTDOWN]
    match = re.search(r'([\d\.]+)s', pause_text)
    if match:
        return float(match.group(1))
    return 1.5

def create_silence(duration_sec, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec),
        "-acodec", "libmp3lame",
        "-b:a", "48k",
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

async def generate_speech_chunk(text, output_mp3, submaker=None, time_offset=0.0):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    with open(output_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary" and submaker is not None:
                # adjust offset if needed
                submaker.feed(chunk)

def format_timestamp_srt(seconds):
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    mins = seconds // 60
    hours = mins // 60
    mins = mins % 60
    secs = seconds % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def format_timestamp_vtt(seconds):
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    mins = seconds // 60
    hours = mins // 60
    mins = mins % 60
    secs = seconds % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d}.{millis:03d}"

async def main():
    print("Reading teleprompter script...")
    with open(TELEPROMPTER_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove header
    parts = content.split("====================================================================")
    body = parts[-1].strip()

    # Split by pause tokens
    tokens = re.split(r'(\[PAUSE\s+[\d\.]+s(?:\s+COUNTDOWN)?\])', body)
    
    file_list = []
    chunk_index = 0
    cumulative_time = 0.0
    timeline_markers = []
    
    print("Processing speech chunks and pauses...")
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
            print(f"Generating speech chunk {chunk_index} ({len(item.split())} words)...")
            await generate_speech_chunk(item, speech_file)
            dur = get_audio_duration(speech_file)
            file_list.append(speech_file)
            timeline_markers.append({
                "type": "speech",
                "duration": dur,
                "start": cumulative_time,
                "end": cumulative_time + dur,
                "text": item
            })
            cumulative_time += dur
            chunk_index += 1

    print(f"\nAll {len(file_list)} audio chunks generated! Total estimated duration: {cumulative_time:.2f}s ({cumulative_time/60:.2f} min)")

    # Concatenate all into full master audio
    concat_list_file = os.path.join(TEMP_DIR, "concat_list.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for fpath in file_list:
            # ffmpeg concat demuxer requires forward slashes or escaped backslashes
            clean_path = fpath.replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    master_audio_path = os.path.join(AUDIO_DIR, "full_voiceover_master.mp3")
    print(f"Concatenating into master file: {master_audio_path} ...")
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
    print(f"Master voiceover created successfully! Final duration: {master_duration:.2f}s ({int(master_duration//60)}m {int(master_duration%60)}s)")

    # Generate Act-specific voiceover files
    # Act 1: chunks up to "It's running an ancient, life-or-death survival simulation."
    # Act 2: chunks up to "...active, five-alarm emergency."
    # Act 3: chunks up to "...won't get you banished into the wilderness."
    # Act 4: chunks up to "...optical illusion created entirely by your own mind."
    # Act 5: chunks to the end
    
    act_definitions = [
        {"act": 1, "end_phrase": "survival simulation."},
        {"act": 2, "end_phrase": "five-alarm emergency."},
        {"act": 3, "end_phrase": "banished into the wilderness."},
        {"act": 4, "end_phrase": "entirely by your own mind."},
        {"act": 5, "end_phrase": "procrastinates."}
    ]
    
    current_act_idx = 0
    current_act_files = []
    
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

    # If any remaining files for Act 5
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
        print(f"  -> Act 5 Voiceover: {act_output} ({act_dur:.1f}s)")

    # Generate complete subtitles (.srt and .vtt)
    srt_path = os.path.join(AUDIO_DIR, "full_voiceover_subtitles.srt")
    vtt_path = os.path.join(AUDIO_DIR, "full_voiceover_subtitles.vtt")
    
    sub_index = 1
    with open(srt_path, "w", encoding="utf-8") as srt_file, open(vtt_path, "w", encoding="utf-8") as vtt_file:
        vtt_file.write("WEBVTT\n\n")
        
        for m in timeline_markers:
            if m["type"] == "speech":
                # split long paragraphs into sentences for readable subtitles
                sentences = re.split(r'(?<=[.?!])\s+', m["text"].strip())
                # estimate time per sentence proportional to length
                total_len = sum(len(s) for s in sentences) if sentences else 1
                seg_start = m["start"]
                seg_dur = m["duration"]
                
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    s_dur = (len(s) / total_len) * seg_dur
                    s_end = seg_start + s_dur
                    
                    # SRT format
                    srt_file.write(f"{sub_index}\n")
                    srt_file.write(f"{format_timestamp_srt(seg_start)} --> {format_timestamp_srt(s_end)}\n")
                    srt_file.write(f"{s}\n\n")
                    
                    # VTT format
                    vtt_file.write(f"{sub_index}\n")
                    vtt_file.write(f"{format_timestamp_vtt(seg_start)} --> {format_timestamp_vtt(s_end)}\n")
                    vtt_file.write(f"{s}\n\n")
                    
                    sub_index += 1
                    seg_start = s_end

    print(f"\nSubtitles created:")
    print(f"  - SRT: {srt_path}")
    print(f"  - VTT: {vtt_path}")

    # Generate Timecode Index Summary
    summary_path = os.path.join(AUDIO_DIR, "VOICEOVER_TIMECODE_INDEX.md")
    with open(summary_path, "w", encoding="utf-8") as sf:
        sf.write("# Master Voiceover Timecode Index\n\n")
        sf.write(f"**Topic:** Why Your Brain Replays Embarrassing Memories at 2 AM\n")
        sf.write(f"**Voice:** `{VOICE}` (Rate: `{RATE}`, Pitch: `{PITCH}`)\n")
        sf.write(f"**Total Audio Runtime:** {int(master_duration//60)}m {int(master_duration%60):02d}s ({master_duration:.2f} seconds)\n\n")
        sf.write("## Audio Files Generated\n\n")
        sf.write("| Track | File | Duration | Description |\n")
        sf.write("|---|---|---|---|\n")
        sf.write(f"| **Full Master Voiceover** | `full_voiceover_master.mp3` | {int(master_duration//60)}m {int(master_duration%60):02d}s | Complete unabridged video voiceover |\n")
        for a in range(1, 6):
            act_p = os.path.join(AUDIO_DIR, f"act{a}_voiceover.mp3")
            if os.path.exists(act_p):
                d = get_audio_duration(act_p)
                sf.write(f"| **Act {a} Voiceover** | `act{a}_voiceover.mp3` | {int(d//60)}m {int(d%60):02d}s | Act {a} standalone audio track |\n")
        sf.write("\n## Subtitle Deliverables\n\n")
        sf.write(f"- SubRip Subtitles: `full_voiceover_subtitles.srt`\n")
        sf.write(f"- WebVTT Subtitles: `full_voiceover_subtitles.vtt`\n")
    print(f"Summary index saved to {summary_path}")

if __name__ == "__main__":
    asyncio.run(main())

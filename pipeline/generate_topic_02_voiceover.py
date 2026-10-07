#!/usr/bin/env python3
"""
pipeline/generate_topic_02_voiceover.py
=======================================
Generates the master high-retention cinematic voiceover for Topic 02:
"The Low Dopamine Morning Routine To Reset Your Brain Focus"

Voice Settings:
- Voice: en-US-ChristopherNeural (Reflective, intellectual, engaging)
- Pitch: +3Hz (User preferred signature pitch for Isy Why)
- Rate: -3% (Calm, authoritative cadence)
- Pacing: Tight, natural conversational flow (0.35s between sentences)
- Act 4 Experiment: Exactly 5.00s thinking space for the 5-second recall test
- Deliverables:
  * Workspace: production/topic_02/audio/TOPIC_02_FULL_VOICEOVER_MASTER.mp3
  * Downloads: C:\\Users\\Indresh HL\\Downloads\\TOPIC_02_FULL_VOICEOVER.mp3
  * Subtitles: C:\\Users\\Indresh HL\\Downloads\\TOPIC_02_CAPTIONS.srt
  * Metadata: production/topic_02/audio/topic_02_timeline_metadata.json
"""

import asyncio
import os
import sys
import re
import json
import subprocess
from pathlib import Path
import edge_tts

# UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

VOICE = "en-US-ChristopherNeural"
RATE = "-3%"
PITCH = "+3Hz"

BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
PROD_AUDIO_DIR = BASE_DIR / "production" / "topic_02" / "audio"
CHUNKS_DIR = PROD_AUDIO_DIR / "chunks"
TEMP_DIR = PROD_AUDIO_DIR / "temp"

DL_DIR = Path(r"C:\Users\Indresh HL\Downloads")
MASTER_MP3_WS = PROD_AUDIO_DIR / "TOPIC_02_FULL_VOICEOVER_MASTER.mp3"
MASTER_MP3_DL = DL_DIR / "TOPIC_02_FULL_VOICEOVER.mp3"
MASTER_SRT_DL = DL_DIR / "TOPIC_02_CAPTIONS.srt"
TIMELINE_JSON = PROD_AUDIO_DIR / "topic_02_timeline_metadata.json"

for d in [PROD_AUDIO_DIR, CHUNKS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Master 29 Script Blocks with Tight Natural Pacing
SCRIPT_BLOCKS = [
    # ACT 1: THE CRIME SCENE AT 6:45 AM (0:00 - 1:30)
    ("LINE_01", "It is 6:45 on a Tuesday morning.", 0.35),
    ("LINE_02", "Your eyes crack open. Your bedroom is still cold. Your muscles feel like lead weights pinned to the mattress.", 0.35),
    ("LINE_03", "And before your conscious mind has even registered what day of the week it is, your hand does what it has done every single morning for the last five years. It reaches for the glass.", 0.35),
    ("LINE_04", "In less than four seconds, a blinding, ten-thousand-lux beam of blue light sears into your retinas. You tell yourself you're just checking the weather. Just checking if that email came through. Just silencing the alarm.", 0.35),
    ("LINE_05", "But thirty minutes later… you are still lying sideways under the covers. You've scrolled through seventeen short-form videos, three political arguments from people you don't know, and a dozen polished photos of lives you aren't living.", 0.35),
    ("LINE_06", "You haven't taken a single step. You haven't brushed your teeth. You haven't even had a glass of water. Yet somehow… your brain feels drained, anxious, and strangely foggy. You feel completely exhausted before your day has even begun.", 0.40),
    ("LINE_07", "Most people believe this morning brain fog is just poor self-discipline. They think they just need more willpower or a stronger cup of coffee. They are completely wrong. What happened in those thirty minutes was not a failure of character. You just walked straight into a neurochemical trap that mathematically sabotaged your brain's ability to focus for the next twelve hours.", 0.50),

    # ACT 2: THE NEUROCHEMICAL HEIST (1:30 - 3:30)
    ("LINE_08", "To understand what you just did to your brain, we have to look at the most misunderstood molecule in modern science: Dopamine. Popular culture calls dopamine the 'pleasure molecule.' But neuroscientists know that dopamine is not about pleasure at all. Dopamine is the neurochemical currency of anticipation, pursuit, and drive.", 0.35),
    ("LINE_09", "In your natural state, your brain maintains what neuroscientists call Tonic Dopamine. This is your baseline circulating level. It is the quiet, steady engine that allows you to read a book, solve a difficult problem, sit in deep conversation, or pursue long-term goals without feeling restless.", 0.35),
    ("LINE_10", "Then there is Phasic Dopamine. First mapped by neurophysiologist Wolfram Schultz at Cambridge, phasic dopamine is a sudden, explosive spike triggered by a Dopamine Prediction Error. Whenever your brain encounters something unexpected, novel, or rewarding, it unleashes a high-voltage surge of phasic dopamine that screams: 'Pay attention to this. This matters for survival.'", 0.35),
    ("LINE_11", "And here is where the catastrophe occurs. As Stanford psychiatrist Doctor Anna Lembke explains in Dopamine Nation, pleasure and pain are processed in the exact same neurological balance scale in your brain. Your brain relentlessly strives for homeostasis—a neutral, stable center.", 0.35),
    ("LINE_12", "For every sudden, artificial spike of dopamine you experience, your brain immediately compensates by slamming down counter-weights of pain and deficit to reset the balance. Receptors downregulate. Neurotransmitter synthesis slows down. When you scroll social media in bed, you receive hundreds of effortless spikes, and your brain's homeostatic response drops your baseline dopamine level below normal.", 0.35),
    ("LINE_13", "So when you sit down at your desk at 9:00 AM to do your actual work, your brain is in an acute neurochemical deficit state. Writing that report or studying that chapter only offers a modest, slow trickle of dopamine. Compared to the artificial skyscraper spike you gave your brain in bed… normal work doesn't just feel boring. It feels biologically repulsive.", 0.50),

    # ACT 3: THE GHOST IN THE MACHINE (3:30 - 5:15)
    ("LINE_14", "But dopamine is only half the crime scene. The second disaster happening inside your morning skull involves two invisible biological currents: Cortisol and Adenosine.", 0.35),
    ("LINE_15", "Within thirty minutes of waking, your endocrine system triggers the Cortisol Awakening Response. This is an ancient, natural surge of cortisol designed to mobilize glucose, raise your body temperature, and gently prepare you for the day's demands. It is meant to be a calm, evolutionary sunrise.", 0.35),
    ("LINE_16", "But when the very first input your waking brain receives is an urgent work email, a catastrophic news headline, or a peer's curated highlight reel… you hijack that gentle sunrise. You convert a healthy awakening response into an acute, full-body threat alert. Your sympathetic nervous system slams on the gas before your conscious mind has even oriented itself in space.", 0.35),
    ("LINE_17", "Even worse: University of Minnesota researcher Doctor Sophie Leroy discovered the principle of Attentional Residue. Whenever your brain switches attention to a new topic—a text message, a headline, a video clip—a portion of your cognitive processing power remains stuck on that previous input. By scanning fifty different pieces of digital content in bed, you shatter your working memory into dozens of microscopic fragments.", 0.35),
    ("LINE_18", "And when you wash that scattered focus down with an immediate cup of coffee, you trap lingering adenosine in your receptors. You haven't cleared the sleep pressure; you've just blindfolded your brain. And by 2:00 in the afternoon, when that blindfold slips off… your focus collapses off a cliff.", 0.50),

    # ACT 4: THE 5-SECOND ATTENTION RESET (5:15 - 7:00)
    ("LINE_19", "Right now, as you watch this video, your brain is doing what it always does: evaluating whether to stay focused, or switch tabs to find a quicker dopamine hit. So let's run a real-time experiment right now to test the state of your attentional hardware.", 0.40),
    ("LINE_20", "I want you to remember the first three apps you opened on your phone this morning. And more importantly: Can you name a single piece of specific, valuable information you learned from them? Think. Five seconds. Starting now.", 5.00), # 5-second interactive thinking pause
    ("LINE_21", "Be honest with yourself. You spent fifteen, thirty, or forty-five minutes consuming digital content before your feet touched the floor. And you can barely recall a single sentence of it.", 0.35),
    ("LINE_22", "You didn't retain that information because your brain wasn't absorbing knowledge. It was simply pulling the lever on a chemical slot machine to numb the discomfort of waking up. That thirty minutes of morning scrolling didn't entertain you. It didn't relax you. It simply stole the highest-value neurochemical window of your entire twenty-four-hour day.", 0.35),
    ("LINE_23", "The first ninety minutes of your morning are when your brain's neuroplasticity is at its absolute peak. Whatever operating state you set during that window becomes the baseline frequency your nervous system tunes to for the rest of the day. If you set your frequency to rapid, high-dopamine distraction… you are trapped in distraction until you sleep. But if you protect that window… you unlock an entirely different level of human focus.", 0.50),

    # ACT 5: THE TACTICAL ANTIDOTE (7:00 - 8:45)
    ("LINE_24", "This is where the Low Dopamine Morning Routine comes in. It is not an extreme monastic punishment. It is not waking up at 4:00 AM to take ice baths and stare at a blank wall. It is a surgical biological protocol built on three non-negotiable rules.", 0.35),
    ("LINE_25", "Rule Number One: The 60-Minute Frictionless Horizon. For the first sixty minutes after opening your eyes, your smartphone does not exist. Do not charge your phone next to your bed. Buy a five-dollar analog alarm clock. By removing the phone from arm's reach, you eliminate the cognitive battle before it begins. No news. No social feeds. No work emails. Protect your baseline dopamine.", 0.35),
    ("LINE_26", "Rule Number Two: The Photon and Hydration Anchor. Within twenty minutes of waking, step outside and get ten to fifteen minutes of natural sunlight into your eyes. Natural photons trigger the melanopsin cells in your retinas, locking in your circadian rhythm and setting a biological timer for optimal melatonin release sixteen hours later. Drink twenty ounces of water to replenish overnight dehydration. And most importantly: Delay your caffeine intake for ninety minutes. Allow your lingering adenosine to naturally clear so you never experience the dreaded 2:00 PM crash.", 0.35),
    ("LINE_27", "Rule Number Three: The Low-Dopamine Runway. Use the final thirty minutes of your morning window to engage in what Cal Newport calls Deep Work. Because you haven't flooded your brain with high-frequency digital junk, your tonic dopamine baseline remains pristine and sensitive. The difficult chapter feels absorbing. The complex problem feels intriguing. You are not fighting your brain for focus—your brain is actively leaning into the challenge.", 0.35),
    ("LINE_28", "The modern world is engineered to auction off your attention to the highest bidder before you've even had time to rub the sleep from your eyes. Every app, algorithm, and notification is competing for the neurochemical fuel that was meant to build your life. Taking back your focus doesn't require superhuman discipline. It just requires you to reclaim the first sixty minutes of your day.", 0.40),
    ("LINE_29", "I'm Isy why. Subscribe, and I'll see you this Monday for the psychological reason your brain procrastinates on what matters most.", 0.50)
]

def create_silence(duration_sec, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec),
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def get_audio_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(res.stdout.strip())

async def generate_speech_with_boundaries(text, output_path, max_retries=5):
    for attempt in range(1, max_retries + 1):
        try:
            communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
            word_boundaries = []
            with open(output_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        word_boundaries.append(chunk)
            await asyncio.sleep(0.2)
            return word_boundaries
        except Exception as e:
            if attempt == max_retries:
                raise e
            wait_time = attempt * 1.5
            print(f"    [!] EdgeTTS retry {attempt}/{max_retries}: {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

def format_timestamp_srt(seconds):
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    mins = seconds // 60
    hours = mins // 60
    mins = mins % 60
    secs = seconds % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

async def main():
    print("=" * 75)
    print("[START] GENERATING TOPIC 02 MASTER HIGH-RETENTION VOICEOVER")
    print(f"Voice: {VOICE} | Pitch: {PITCH} | Rate: {RATE}")
    print("Pacing: Tight conversational pauses (0.35s) + Act 4 5-sec countdown space")
    print("=" * 75)

    concat_list_file = TEMP_DIR / "concat_list.txt"
    concat_lines = []
    
    timeline_records = []
    srt_entries = []
    cumulative_time = 0.0

    total_blocks = len(SCRIPT_BLOCKS)
    print(f"[*] Processing {total_blocks} script lines with natural conversational pacing...")

    for idx, (label, text, pause_dur) in enumerate(SCRIPT_BLOCKS, 1):
        speech_file = CHUNKS_DIR / f"{idx:02d}_{label}_speech.mp3"
        
        # Generate speech
        word_boundaries = await generate_speech_with_boundaries(text, speech_file)
        dur_speech = get_audio_duration(speech_file)
        concat_lines.append(f"file '{speech_file.as_posix()}'")

        start_time = cumulative_time
        end_time = cumulative_time + dur_speech

        # Build SRT entry
        srt_idx = len(srt_entries) + 1
        srt_start = format_timestamp_srt(start_time)
        srt_end = format_timestamp_srt(end_time)
        # Format text clean for subtitles
        sub_text = text.replace("…", "...").replace("—", " - ")
        srt_entries.append(f"{srt_idx}\n{srt_start} --> {srt_end}\n{sub_text}\n")

        # Record timeline record
        timeline_records.append({
            "line_index": idx,
            "line_label": label,
            "text": text,
            "speech_duration": dur_speech,
            "pause_duration": pause_dur,
            "start_time": start_time,
            "end_time": end_time
        })

        cumulative_time += dur_speech

        # Add pause
        if pause_dur > 0:
            silence_file = TEMP_DIR / f"pause_{idx:02d}_{pause_dur:.2f}s.mp3"
            create_silence(pause_dur, silence_file)
            concat_lines.append(f"file '{silence_file.as_posix()}'")
            cumulative_time += pause_dur

        print(f"  [{idx:02d}/{total_blocks}] {label} ({dur_speech:5.2f}s speech + {pause_dur:4.2f}s pause) | Start: {start_time:6.2f}s -> {text[:42]}...")

    # Write concat manifest
    with open(concat_list_file, "w", encoding="utf-8") as f:
        f.write("\n".join(concat_lines))

    # Assemble master MP3
    print("\n[*] Assembling full master voiceover with FFmpeg (192 kbps)...")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(MASTER_MP3_WS)
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Copy to Downloads
    import shutil
    shutil.copy2(MASTER_MP3_WS, MASTER_MP3_DL)

    # Write SRT
    with open(MASTER_SRT_DL, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    # Save timeline metadata
    with open(TIMELINE_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "topic": "Topic 02: The Low Dopamine Morning Routine To Reset Your Brain Focus",
            "voice": VOICE,
            "rate": RATE,
            "pitch": PITCH,
            "total_lines": total_blocks,
            "total_duration": cumulative_time,
            "lines": timeline_records
        }, f, indent=2)

    total_duration = get_audio_duration(MASTER_MP3_WS)
    mins = int(total_duration // 60)
    secs = int(total_duration % 60)

    print("\n" + "=" * 75)
    print("[SUCCESS] TOPIC 02 VOICE GENERATION COMPLETE!")
    print(f"• Total Runtime:   {mins}m {secs:02d}s ({total_duration:.2f} seconds)")
    print(f"• Voice Model:     {VOICE} (Pitch: {PITCH}, Rate: {RATE})")
    print(f"• Pacing Standard: Tight natural 0.35s conversational pauses")
    print(f"• Act 4 Space:     5.00s thinking space on Line 20")
    print(f"• Master Audio:    {MASTER_MP3_DL}")
    print(f"• SRT Subtitles:   {MASTER_SRT_DL}")
    print(f"• Metadata JSON:   {TIMELINE_JSON}")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(main())

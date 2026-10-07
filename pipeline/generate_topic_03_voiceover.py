import asyncio
import os
import sys
import re
import subprocess
from pathlib import Path
import edge_tts

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Audio settings
VOICE = "en-US-ChristopherNeural"
RATE = "-3%"
PITCH = "+3Hz"  # User preferred pitch from Topic 02

BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
PROD_AUDIO_DIR = BASE_DIR / "production" / "topic_03" / "audio"
CHUNKS_DIR = PROD_AUDIO_DIR / "chunks"
TEMP_DIR = PROD_AUDIO_DIR / "temp"

DL_DIR = Path(r"C:\Users\Indresh HL\Downloads")
MASTER_MP3_WS = PROD_AUDIO_DIR / "TOPIC_03_FULL_VOICEOVER_MASTER.mp3"
MASTER_MP3_DL = DL_DIR / "TOPIC_03_FULL_VOICEOVER.mp3"
MASTER_SRT_DL = DL_DIR / "TOPIC_03_CAPTIONS.srt"

for d in [PROD_AUDIO_DIR, CHUNKS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Master script lines with natural conversational pauses (0.35s normal, 1.0s ticks during countdown)
SCRIPT_BLOCKS = [
    # ACT 1
    ("LINE_01", "It is 11:42 on a Tuesday night. In less than nine hours, that major project is due.", 0.35),
    ("LINE_02", "You open your laptop. A blank white screen stares back at you. And in the corner, a single black cursor blinks. Steadily. Mockingly.", 0.35),
    ("LINE_03", "Your fingers hover over the keyboard. But instead of typing the first sentence, your hand reaches for your phone. You open an app you don’t even care about, scrolling through videos you won’t remember ten seconds from now.", 0.35),
    ("LINE_04", "You aren’t enjoying yourself. There is no joy in this scrolling. Your stomach feels tight, your chest feels heavy, and that familiar, sickening wave of shame begins to creep up your throat.", 0.35),
    ("LINE_05", "You whisper to yourself: \"Why do I do this every single time? Why am I so lazy? Why can’t I just sit down and do the work?\"", 0.40),
    ("LINE_06", "If that scene feels uncomfortably familiar, I want you to take a deep breath. Because modern cognitive neuroscience has discovered something extraordinary about this moment.", 0.35),
    ("LINE_07", "Your chronic procrastination has almost nothing to do with being lazy. It is not a character flaw. And no amount of color-coded planners or calendar apps will ever cure it.", 0.35),
    ("LINE_08", "What you experienced at 11:42 PM wasn't laziness. It was an involuntary biological defense mechanism. Your brain perceived that blank document not as a to-do list, but as an existential threat. And without your conscious permission, it triggered a full-scale neurological ambush.", 0.50),

    # ACT 2
    ("LINE_09", "Inside your skull, there is a constant power struggle between two very different evolutionary systems.", 0.35),
    ("LINE_10", "First, you have your prefrontal cortex. This is the newest, most civilized part of your brain. It understands time. It cares about your future. It knows that finishing this report tonight means freedom, success, and peace of mind tomorrow.", 0.35),
    ("LINE_11", "But buried deep beneath it lies the amygdala and the limbic system. This ancient survival engine doesn't understand calendars, college degrees, or quarterly reviews. It only understands one question: \"Is this safe right now?\"", 0.40),
    ("LINE_12", "And here is the core discovery uncovered by psychologists Doctor Tim Pychyl and Doctor Fuschia Sirois: Procrastination is an emotional regulation problem, not a time management problem.", 0.35),
    ("LINE_13", "When you look at an important task, it isn't the physical keyboard you fear. It's the painful emotions attached to it: the fear that your work won't be good enough, the terror of judgment, or the crushing weight of perfectionism.", 0.35),
    ("LINE_14", "To your ancient amygdala, psychological discomfort feels identical to physical danger. So it executes a rapid evolutionary maneuver called \"mood repair.\" It forces you to abandon the threatening task and seek immediate comfort. The moment you decide, \"I'll just do this tomorrow,\" your amygdala relaxes. The cortisol drops. A small squirt of dopamine enters your bloodstream. You feel instant, intoxicating relief.", 0.35),
    ("LINE_15", "But that relief is counterfeit. Because by running away from the negative emotion today, you have not solved the problem. You have simply passed the debt forward. And that brings us to the most shocking neurological secret of all: Who exactly did you pass that debt to?", 0.50),

    # ACT 3
    ("LINE_16", "At UCLA, social psychologist Doctor Hal Hershfield put human participants into fMRI brain scanners to investigate how the brain visualizes time.", 0.35),
    ("LINE_17", "When researchers asked people to think about who they are right now—their current feelings, their current hunger, their current stress—a specific region called the medial prefrontal cortex lit up like a Christmas tree.", 0.35),
    ("LINE_18", "Next, they asked participants to think about a total stranger: a random person waiting for a bus in another city. As expected, that self-processing neural circuit powered down completely.", 0.35),
    ("LINE_19", "Then came the breakthrough. Hershfield asked participants to think about their future self—the version of them that would exist in ten years, next month, or even tomorrow morning. Neurologically, something jaw-dropping happened.", 0.40),
    ("LINE_20", "The brain processed the future self in the exact same pattern it used for a complete stranger. To your subconscious mind, Tomorrow You is not you. Tomorrow You is an unfamiliar person who can handle all the stress, exhaustion, and pain that you don't feel like dealing with tonight.", 0.35),
    ("LINE_21", "You tell yourself: \"Tomorrow Sam will have superhuman discipline. Tomorrow Sam will wake up at 6:00 AM full of energy and write that ten-page paper in two hours.\"", 0.35),
    ("LINE_22", "But tomorrow morning arrives. And the cruel joke is revealed: That stranger is you.", 0.40),
    ("LINE_23", "You inherited the debt, you inherited the exhaustion, and now you have less time than you started with. So why does this loop feel impossible to escape?", 0.50),

    # ACT 4
    ("LINE_24", "I want to run a quick, real-time experiment with you right now. Do not skip forward. Do not look away from this screen.", 0.35),
    ("LINE_25", "In the next five seconds, think about the one single project, phone call, or chore that you have been putting off for the past week. Bring it into your mind right now.", 0.80),
    # 5-second countdown interactive thinking space:
    ("LINE_26_5", "Five.", 1.00),
    ("LINE_26_4", "Four.", 1.00),
    ("LINE_26_3", "Three.", 1.00),
    ("LINE_26_2", "Two.", 1.00),
    ("LINE_26_1", "One.", 0.80),
    ("LINE_27", "Notice what happened in your body the moment that task flashed in your mind. Did your breathing shallow out? Did you feel a tiny knot in your solar plexus? Did an internal voice whisper, \"I'll do that later tonight\"?", 0.35),
    ("LINE_28", "That micro-flinch is the exact friction that keeps millions of people trapped for years. In chemistry, there is a fundamental law known as Activation Energy: the minimum amount of energy required to start a reaction.", 0.35),
    ("LINE_29", "When you define your task as \"Write my master’s thesis\" or \"Clean the entire house,\" the activation energy is colossal. Your amygdala looks at that gigantic boulder, sounds the emergency sirens, and locks your muscles in place.", 0.35),
    ("LINE_30", "But once a chemical reaction begins, it releases its own energy. The entire secret to defeating chronic procrastination is not building superhuman willpower. It is reducing the activation energy until your amygdala can't even see the task.", 0.35),
    ("LINE_31", "So how do we outsmart hundreds of thousands of years of evolutionary wiring? We use two precise, scientifically verified micro-habit protocols.", 0.50),

    # ACT 5
    ("LINE_32", "Protocol One is the Two-Minute Gateway, popularized by behavioral scientist BJ Fogg and author James Clear. The rule is deceptively simple: You are not allowed to do the full task. You are only allowed to perform the first two minutes.", 0.35),
    ("LINE_33", "You aren’t writing a 2,000-word essay. Your only goal is to write one sentence. You aren’t doing a 45-minute workout. Your only goal is to put on your running shoes and tie the laces. You aren't reading an entire textbook. You're reading three bullet points.", 0.35),
    ("LINE_34", "Why does this work? Because one sentence is so laughably small that your amygdala does not register it as an emotional threat. The alarm stays silent. You bypass the security guard without triggering a fight-or-flight response.", 0.35),
    ("LINE_35", "And once you cross that microscopic threshold of initiation, physics takes over. Sir Isaac Newton wasn't just describing apples; he was describing psychology: An object in motion tends to stay in motion. Starting was the only monster in the room.", 0.35),
    ("LINE_36", "But there is a second, even more important protocol. And it comes from Doctor Fuschia Sirois’s landmark research on self-compassion. Most people believe that punishing themselves with guilt will force them to work harder tomorrow.", 0.35),
    ("LINE_37", "Science proves the exact opposite: Self-blame triggers the very negative emotions that drive you right back into the arms of procrastination. Forgiving yourself for the hours you wasted yesterday actually decreases your likelihood of procrastinating today. You don't cure resistance with cruelty; you cure it by taking the shame out of starting.", 0.35),
    ("LINE_38", "Tonight, when that cursor blinks in the dark, don't wage war on yourself. Lower the bar. Make the task tiny. And remember: You aren't lazy. You're just human learning to speak the language of your own biology.", 0.40),
    ("LINE_39", "I'll see you on Friday. Stay curious.", 0.50)
]

def create_silence(duration_sec, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec),
        "-acodec", "libmp3lame",
        "-b:a", "128k",
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

async def generate_speech(text, output_path, max_retries=5):
    if output_path.exists() and output_path.stat().st_size > 1000:
        return
    for attempt in range(1, max_retries + 1):
        try:
            communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
            await communicate.save(str(output_path))
            await asyncio.sleep(0.25)  # polite spacing to keep websocket healthy
            return
        except Exception as e:
            if attempt == max_retries:
                raise e
            wait_time = attempt * 1.5
            print(f"    [!] Connection hiccup on '{output_path.name}' (Attempt {attempt}/{max_retries}): {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

async def main():
    print("=" * 70)
    print("[START] GENERATING TOPIC 03 NATURAL BROADCAST VOICEOVER")
    print(f"Voice: {VOICE} | Pitch: {PITCH} | Rate: {RATE}")
    print("=" * 70)

    concat_list_file = TEMP_DIR / "concat_list.txt"
    concat_lines = []
    
    total_blocks = len(SCRIPT_BLOCKS)
    print(f"[*] Processing {total_blocks} script lines with natural conversational pauses...")

    for idx, (label, text, pause_dur) in enumerate(SCRIPT_BLOCKS, 1):
        speech_file = CHUNKS_DIR / f"{idx:02d}_{label}_speech.mp3"
        
        # 1. Generate speech chunk with retries
        await generate_speech(text, speech_file)
        dur_speech = get_audio_duration(speech_file)
        concat_lines.append(f"file '{speech_file.as_posix()}'")

        # 2. Add subtle natural breath pause
        if pause_dur > 0:
            silence_file = TEMP_DIR / f"pause_{idx:02d}_{pause_dur:.2f}s.mp3"
            create_silence(pause_dur, silence_file)
            concat_lines.append(f"file '{silence_file.as_posix()}'")

        print(f"  [{idx:02d}/{total_blocks}] {label} ({dur_speech:.2f}s + {pause_dur:.2f}s pause): {text[:45]}...")

    # Write ffmpeg concat manifest
    with open(concat_list_file, "w", encoding="utf-8") as f:
        f.write("\n".join(concat_lines))

    # 3. Concatenate into master audio file
    print("\n[*] Assembling full master voiceover with FFmpeg...")
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

    # Copy to user's Downloads folder
    import shutil
    shutil.copy2(MASTER_MP3_WS, MASTER_MP3_DL)

    total_duration = get_audio_duration(MASTER_MP3_WS)
    mins = int(total_duration // 60)
    secs = int(total_duration % 60)

    print("\n" + "=" * 70)
    print("[SUCCESS] FULL VOICEOVER GENERATION COMPLETE!")
    print(f"• Total Runtime:   {mins}m {secs:02d}s ({total_duration:.2f} seconds)")
    print(f"• Bitrate:         192 kbps MP3 (Studio Quality)")
    print(f"• Workspace File:  {MASTER_MP3_WS}")
    print(f"• Downloads File:  {MASTER_MP3_DL}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

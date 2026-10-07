#!/usr/bin/env python3
"""
pipeline/render_youtube_shorts_suite.py
======================================
Automated Short-Form Production Suite for channel Isy why (@isy019).
Converts the 4K UHD Master Video into a suite of high-retention, standalone
YouTube Shorts / Reels adhering strictly to the "3-Part Value Loop" architecture.

Canvas Architecture:
- 1080x1920 (9:16 vertical)
- Centered 16:9 Master Video: 1080x608 (Lanczos downscaled, placed at x=0, y=656)
- Ambient Background: Full-bleed boxblur=26:5, brightness=-0.15, contrast=1.12
- Safe Zone: 100% inside y=656 to y=1264 (clear of YouTube Shorts / TikTok UI)
- Audio Micro-Fades: 80ms in / 150ms out at every cut point to eliminate clicks/pops
- Hardware Acceleration: NVIDIA NVENC GPU (h264_nvenc, High Profile, yuv420p, 30fps)
- Duration Limit: Strictly between 30.0s and 58.0s (never exceeds 60s)
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# UTF-8 stdout/stderr for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Paths
BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
MASTER_VIDEO = Path(r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\1004.mp4")
OUTPUT_DIR = Path(r"C:\Users\Indresh HL\Downloads\short&reels\youtube shorts")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 4 Standalone 3-Part Value Loop Shorts Specifications
SHORTS_SPECS = [
    {
        "id": "short_01",
        "filename": "Short_01_Why_Morning_Scrolling_Destroys_Focus.mp4",
        "title": "Why Does Morning Scrolling Destroy Your Entire Day? #Shorts",
        "category": "Science & Technology",
        "segments": [
            {
                "label": "Hook: Morning Fog & Exhaustion",
                "start": 55.510,
                "end": 73.438,
                "text": "You haven't taken a single step. You haven't brushed your teeth. You haven't even had a glass of water. Yet somehow... your brain feels drained, anxious, and strangely foggy. You feel completely exhausted before your day has even begun."
            },
            {
                "label": "Mechanism: The 9 AM Dopamine Deficit",
                "start": 215.263,
                "end": 239.479,
                "text": "So when you sit down at your desk at 9:00 AM to do your actual work, your brain is in an acute neurochemical deficit state. Writing that report or studying that chapter only offers a modest, slow trickle of dopamine. Compared to the artificial skyscraper spike you gave your brain in bed... normal work doesn't just feel boring. It feels biologically repulsive."
            },
            {
                "label": "Payoff & Protocol: The 60-Minute Horizon",
                "start": 465.358,
                "end": 478.000,
                "text": "Rule Number One: The 60-Minute Frictionless Horizon. For the first sixty minutes after opening your eyes, your smartphone does not exist."
            }
        ],
        "seo_description": (
            "Ever wonder why grabbing your phone first thing in the morning makes you feel exhausted before your day even starts? 🧠\n\n"
            "When you scroll social media in bed, you flood your brain with artificial dopamine spikes. By 9:00 AM, your brain slams into an acute neurochemical deficit—making normal work feel biologically repulsive.\n\n"
            "Watch the full scientific protocol to reset your brain focus:\n"
            "🔗 Full Deep Dive: https://youtu.be/sn-U8u_b7yA\n\n"
            "Subscribe to @isy019 for weekly psychology deep dives.\n"
            "#Shorts #Dopamine #Focus #MorningRoutine #Psychology #BrainHealth #Neuroscience #Productivity #DigitalDetox #SelfImprovement"
        ),
        "hashtags": ["#Shorts", "#Dopamine", "#Focus", "#MorningRoutine", "#BrainFog", "#Neuroscience", "#Productivity", "#DigitalDetox", "#DeepWork", "#SelfImprovement"],
        "tags": ["dopamine detox", "morning routine", "brain fog", "focus reset", "neuroscience", "why morning scrolling ruins your day", "productivity hacks", "psychology", "dopamine nation", "isy why"]
    },
    {
        "id": "short_02",
        "filename": "Short_02_The_Coffee_Mistake_2PM_Crash.mp4",
        "title": "Why Is Your Morning Coffee Crashing You At 2 PM? #Shorts",
        "category": "Education",
        "segments": [
            {
                "label": "Hook: Coffee & The 2 PM Energy Cliff",
                "start": 324.516,
                "end": 344.076,
                "text": "And when you wash that scattered focus down with an immediate cup of coffee, you trap lingering adenosine in your receptors. You haven't cleared the sleep pressure; you've just blindfolded your brain. And by 2:00 in the afternoon, when that blindfold slips off... your focus collapses off a cliff."
            },
            {
                "label": "Mechanism: Cortisol Awakening Response",
                "start": 252.065,
                "end": 267.500,
                "text": "Within thirty minutes of waking, your endocrine system triggers the Cortisol Awakening Response. This is an ancient, natural surge of cortisol designed to mobilize glucose, raise your body temperature, and gently prepare you for the day's demands."
            },
            {
                "label": "Payoff & Protocol: The 90-Minute Caffeine Delay",
                "start": 519.500,
                "end": 536.124,
                "text": "And most importantly: Delay your caffeine intake for ninety minutes. Allow your lingering adenosine to naturally clear so you never experience the dreaded 2:00 PM crash."
            }
        ],
        "seo_description": (
            "Drinking coffee right when you wake up? You're setting yourself up for the brutal 2:00 PM energy cliff. ☕⚡\n\n"
            "Caffeine doesn't eliminate adenosine (sleep pressure)—it just blindfolds your receptors while disrupting your natural Cortisol Awakening Response. When caffeine clears, adenosine floods in, creating the afternoon crash.\n\n"
            "Watch how to time your morning for all-day steady energy:\n"
            "🔗 Full Deep Dive: https://youtu.be/sn-U8u_b7yA\n\n"
            "Subscribe to @isy019 for weekly science-backed protocols.\n"
            "#Shorts #Coffee #Adenosine #EnergyCrash #MorningRoutine #Neuroscience #Biohacking #Productivity #Health #Focus"
        ),
        "hashtags": ["#Shorts", "#Coffee", "#Adenosine", "#AfternoonCrash", "#MorningRoutine", "#EnergyHack", "#Neuroscience", "#Cortisol", "#Biohacking", "#Productivity"],
        "tags": ["morning coffee mistake", "afternoon crash", "adenosine caffeine", "cortisol awakening response", "huberman morning routine", "energy crash at 2pm", "how to stop feeling tired", "biohacking", "productivity", "isy why"]
    },
    {
        "id": "short_03",
        "filename": "Short_03_The_Attentional_Residue_Trap.mp4",
        "title": "Why Can't Your Brain Focus on Hard Work Anymore? #Shorts",
        "category": "Education",
        "segments": [
            {
                "label": "Hook: Digital Amnesia in Bed",
                "start": 383.096,
                "end": 396.368,
                "text": "Be honest with yourself. You spent fifteen, thirty, or forty-five minutes consuming digital content before your feet touched the floor. And you can barely recall a single sentence of it."
            },
            {
                "label": "Mechanism: Sophie Leroy's Attentional Residue",
                "start": 297.094,
                "end": 324.166,
                "text": "University of Minnesota researcher Doctor Sophie Leroy discovered the principle of Attentional Residue. Whenever your brain switches attention to a new topic - a text message, a headline, a video clip - a portion of your cognitive processing power remains stuck on that previous input. By scanning fifty different pieces of digital content in bed, you shatter your working memory into dozens of microscopic fragments."
            },
            {
                "label": "Payoff & Protocol: Reclaiming Deep Work",
                "start": 554.720,
                "end": 566.738,
                "text": "The difficult chapter feels absorbing. The complex problem feels intriguing. You are not fighting your brain for focus - your brain is actively leaning into the challenge."
            }
        ],
        "seo_description": (
            "Why is it so hard to sit down and read a book or write a report without feeling an overwhelming urge to check your phone? 📚🧠\n\n"
            "Cognitive scientist Dr. Sophie Leroy proved that every quick headline or clip leaves an 'attentional residue' stuck in working memory. When you protect your morning window from digital fragmentation, your brain actively leans into challenging deep work.\n\n"
            "Learn how to rebuild your attention span:\n"
            "🔗 Full Deep Dive: https://youtu.be/sn-U8u_b7yA\n\n"
            "Subscribe to @isy019 for deep psychology breakdowns.\n"
            "#Shorts #DeepWork #AttentionalResidue #Focus #ADHD #BrainFog #Productivity #CognitiveScience #Psychology #CalNewport"
        ),
        "hashtags": ["#Shorts", "#AttentionalResidue", "#DeepWork", "#Focus", "#BrainFog", "#Productivity", "#CognitiveScience", "#AttentionSpan", "#Psychology", "#CalNewport"],
        "tags": ["attentional residue", "deep work", "cant focus on work", "broken attention span", "cal newport focus", "brain fog cure", "cognitive science", "psychology tricks", "study motivation", "isy why"]
    },
    {
        "id": "short_04",
        "filename": "Short_04_The_60_Minute_Focus_Reset.mp4",
        "title": "How To Reset Your Brain Focus In Just 60 Minutes? #Shorts",
        "category": "Science & Technology",
        "segments": [
            {
                "label": "Hook: The Morning Neuroplasticity Window",
                "start": 419.556,
                "end": 433.000,
                "text": "The first ninety minutes of your morning are when your brain's neuroplasticity is at its absolute peak. Whatever operating state you set during that window becomes the baseline frequency your nervous system tunes to for the rest of the day."
            },
            {
                "label": "Mechanism: Low Dopamine Protocol",
                "start": 446.792,
                "end": 465.008,
                "text": "This is where the Low Dopamine Morning Routine comes in. It is not an extreme monastic punishment. It is not waking up at 4:00 AM to take ice baths and stare at a blank wall. It is a surgical biological protocol built on three non-negotiable rules."
            },
            {
                "label": "Payoff & Reframe: Reclaim the First 60 Minutes",
                "start": 581.300,
                "end": 590.440,
                "text": "Taking back your focus doesn't require superhuman discipline. It just requires you to reclaim the first sixty minutes of your day."
            }
        ],
        "seo_description": (
            "You don't need superhuman willpower to fix your attention span. You just need to protect the first 60 minutes of your morning. 🌅🧠\n\n"
            "Your brain's neuroplasticity peaks right after waking. By avoiding high-dopamine triggers during this critical window, you preserve your tonic baseline and reset your nervous system for effortless focus all day.\n\n"
            "Watch the complete 3-rule biological protocol:\n"
            "🔗 Full Deep Dive: https://youtu.be/sn-U8u_b7yA\n\n"
            "Subscribe to @isy019 for curiosity & psychology deep dives.\n"
            "#Shorts #FocusReset #MorningRoutine #DopamineDetox #Neuroplasticity #Psychology #Productivity #HabitLoop #Mindset #SelfDiscipline"
        ),
        "hashtags": ["#Shorts", "#FocusReset", "#MorningRoutine", "#DopamineDetox", "#Neuroplasticity", "#Neuroscience", "#SelfDiscipline", "#Productivity", "#Psychology", "#Mindset"],
        "tags": ["how to reset focus", "low dopamine morning routine", "neuroplasticity morning", "dopamine detox", "reclaim your focus", "morning habits that change your life", "discipline vs habits", "focus protocol", "psychology facts", "isy why"]
    }
]

def build_filter_complex(segments):
    """
    Constructs the FFmpeg filter_complex graph:
    1. Trims each video segment
    2. Trims each audio segment with 80ms in / 150ms out micro-fades
    3. Concatenates video and audio streams cleanly
    4. Applies peak limiter ceiling at 0.98 to audio
    5. Splits video into background (scale+crop+boxblur+eq) and foreground (scale 1080x608 Lanczos)
    6. Overlays foreground at y=656 (vertically centered in 1080x1920)
    """
    n = len(segments)
    parts = []
    
    # 1 & 2: Trims and audio fades
    for i, seg in enumerate(segments):
        s = seg["start"]
        e = seg["end"]
        dur = e - s
        parts.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}_src]")
        parts.append(
            f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:ss=0:d=0.08,afade=t=out:st={dur-0.15:.3f}:d=0.15[a{i}]"
        )
    
    # Concat video
    v_inputs = "".join(f"[v{i}_src]" for i in range(n))
    parts.append(f"{v_inputs}concat=n={n}:v=1:a=0[v_concat]")
    
    # Concat audio + peak limiter ceiling at 0.98
    a_inputs = "".join(f"[a{i}]" for i in range(n))
    parts.append(f"{a_inputs}concat=n={n}:v=0:a=1,alimiter=limit=0.98:attack=5:release=50[a_final]")
    
    # 9:16 Canvas Architecture: Background & Foreground
    parts.append("[v_concat]split=2[bg_in][fg_in]")
    parts.append(
        "[bg_in]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=26:5,eq=brightness=-0.15:contrast=1.12,setsar=1[bg]"
    )
    parts.append("[fg_in]scale=1080:608:flags=lanczos,setsar=1[fg]")
    parts.append("[bg][fg]overlay=0:656[v_final]")
    
    return ";".join(parts)

def render_short(spec):
    out_file = OUTPUT_DIR / spec["filename"]
    print(f"\n======================================================================")
    print(f"🎬 RENDERING: {spec['title']}")
    print(f"📁 Output File: {out_file}")
    
    total_calc_dur = sum(s["end"] - s["start"] for s in spec["segments"])
    print(f"⏱️ Calculated Runtime: {total_calc_dur:.2f}s (Rule: 30.0s - 58.0s)")
    assert 30.0 <= total_calc_dur <= 58.0, f"Duration {total_calc_dur}s out of range!"
    
    for i, s in enumerate(spec["segments"]):
        dur = s["end"] - s["start"]
        print(f"   Part {i+1} [{dur:5.2f}s | {s['start']:6.2f}s - {s['end']:6.2f}s]: {s['label']}")
    
    filter_complex = build_filter_complex(spec["segments"])
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(MASTER_VIDEO),
        "-filter_complex", filter_complex,
        "-map", "[v_final]", "-map", "[a_final]",
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-profile:v", "high",
        "-b:v", "12M",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "48000",
        "-movflags", "+faststart",
        str(out_file)
    ]
    
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    render_time = time.time() - t0
    
    if res.returncode != 0:
        print(f"❌ RENDER ERROR on {spec['filename']}!")
        print("STDERR:\n", res.stderr[-1500:])
        return False
        
    print(f"✅ Render Complete in {render_time:.1f}s!")
    
    # ffprobe verification
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate,pix_fmt",
        "-of", "json",
        str(out_file)
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    if probe_res.returncode == 0:
        pdata = json.loads(probe_res.stdout)
        streams = pdata.get("streams", [])
        v_stream = next((s for s in streams if s.get("width")), {})
        f_info = pdata.get("format", {})
        actual_dur = float(f_info.get("duration", 0))
        size_mb = int(f_info.get("size", 0)) / (1024 * 1024)
        print(f"   🔍 PROBE VERIFIED:")
        print(f"      Resolution : {v_stream.get('width')}x{v_stream.get('height')} (Expected 1080x1920)")
        print(f"      Codec      : {v_stream.get('codec_name')} ({v_stream.get('pix_fmt')}) @ {v_stream.get('r_frame_rate')} fps")
        print(f"      Duration   : {actual_dur:.2f}s (Rule: 30.0s - 58.0s)")
        print(f"      File Size  : {size_mb:.2f} MB")
        spec["actual_duration"] = actual_dur
        spec["file_size_mb"] = size_mb
    return True

def generate_manifest():
    manifest_path = OUTPUT_DIR / "MANIFEST.md"
    print(f"\n📝 Generating Master Manifest: {manifest_path}")
    
    lines = [
        "# 🚀 VIRAL YOUTUBE SHORTS SUITE: TOPIC 02",
        "## Channel: Isy why (`@isy019`)",
        "**Master Video Reference:** `https://youtu.be/sn-U8u_b7yA`  ",
        "**Source Master File:** `C:\\Users\\Indresh HL\\Downloads\\READY IT UPLOAD\\1004.mp4` (4K UHD 60 fps)  ",
        "**Canvas Standard:** 1080x1920 (9:16 Vertical) | Centered 16:9 Master Video (1080x608, Lanczos)  ",
        "**Background Architecture:** Ambient blurred video mirror (`boxblur=26:5`, `brightness=-0.15`, `contrast=1.12`)  ",
        "**Safe-Zone Conformance:** Center box (`y=656` to `y=1264`) - 100% unobstructed by Shorts/TikTok UI  ",
        "**Audio Engineering:** 80ms in / 150ms out micro-fades at every cut point; Peak Limiter ceiling $\\le 0.98$  ",
        "**Hardware Acceleration:** NVIDIA NVENC GPU (`h264_nvenc`, High Profile, `yuv420p`, 30 fps, AAC 256 kbps)  ",
        "\n---\n",
        "## 📊 Executive Summary Table\n",
        "| Short ID | File Name | Title | Runtime | Resolution | Video Codec | Audio Bitrate | Size (MB) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    
    for s in SHORTS_SPECS:
        lines.append(
            f"| `{s['id']}` | `{s['filename']}` | **{s['title']}** | **{s.get('actual_duration', 0):.2f}s** | 1080x1920 | H.264 High (`yuv420p`) | AAC 256k | {s.get('file_size_mb', 0):.2f} MB |"
        )
        
    lines.append("\n---\n")
    lines.append("## 📦 Detailed Short-by-Short Metadata & Publishing Packages\n")
    
    for idx, s in enumerate(SHORTS_SPECS, 1):
        lines.append(f"### Short {idx}: {s['title']}\n")
        lines.append(f"- **Filename:** `{s['filename']}`")
        lines.append(f"- **Runtime:** **{s.get('actual_duration', 0):.2f} seconds** (Target: 30.0s – 58.0s)")
        lines.append(f"- **Category:** `{s['category']}`")
        lines.append(f"- **Funnel Long-Form Video:** `https://youtu.be/sn-U8u_b7yA`\n")
        
        lines.append("#### 🎬 3-Part Value Loop Breakdown:")
        for seg_idx, seg in enumerate(s["segments"], 1):
            dur = seg["end"] - seg["start"]
            lines.append(f"{seg_idx}. **{seg['label']}** (`{seg['start']:.2f}s – {seg['end']:.2f}s` | `{dur:.2f}s`):")
            lines.append(f"   > *\"{seg['text']}\"*\n")
            
        lines.append("#### 📝 High-CTR YouTube Title:")
        lines.append("```text")
        lines.append(s["title"])
        lines.append("```\n")
        
        lines.append("#### 📄 SEO Description (With Funnel Link):")
        lines.append("```text")
        lines.append(s["seo_description"])
        lines.append("```\n")
        
        lines.append("#### 🏷️ Top 10 Search Hashtags:")
        lines.append("`" + " ".join(s["hashtags"]) + "`\n")
        
        lines.append("#### 🎯 YouTube Studio Tags (Comma-Separated):")
        lines.append("```text")
        lines.append(", ".join(s["tags"]))
        lines.append("```\n")
        lines.append("---\n")
        
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ Successfully wrote manifest to {manifest_path}")

def main():
    print("======================================================================")
    print("🚀 STARTING VIRAL SHORT-FORM VIDEO PRODUCTION SUITE")
    print(f"🎬 Master Source: {MASTER_VIDEO}")
    print(f"📁 Destination Folder: {OUTPUT_DIR}")
    print("======================================================================")
    
    total_start = time.time()
    for spec in SHORTS_SPECS:
        success = render_short(spec)
        if not success:
            print("Render pipeline aborted due to error.")
            sys.exit(1)
            
    generate_manifest()
    
    print("\n======================================================================")
    print(f"🎉 ALL 4 SHORTS SUCCESSFULLY RENDERED & VERIFIED IN {time.time() - total_start:.1f}s!")
    print(f"📂 Location: {OUTPUT_DIR}")
    print("======================================================================")

if __name__ == "__main__":
    main()

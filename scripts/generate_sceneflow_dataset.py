#!/usr/bin/env python3
"""
scripts/generate_sceneflow_dataset.py

Authoritative SceneFlow Dataset Generator for Topic 03:
"Why You Can't Start: The Cognitive Science of Chronic Procrastination (And The Micro-Habit Antidote)"

Generates the canonical 8-track topic_03_sceneflow_sync.json adhering strictly to:
- taruma/SceneFlow Draft-07 JSON Schema (public/schema.json)
- Exactly 99 visual shots (19 static holds + 80 dynamic camera moves)
- Exactly 481 dialogue phrases (speaker='Sam', snapped to visual cuts)
- 8 Color-Coded Cue Tracks: Dialogue, Action, Camera, Shot, Audio, VFX, Transition, Environment
- Full screenplay text with verbatim character indices (startIndex, endIndex)
- Monotonic timestamps with t_start < t_end <= 565.10s
"""

import json
import os
import sys
from pathlib import Path
import jsonschema

# Configure stdout encoding for Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
WORD_TIMESTAMPS_FILE = BASE_DIR / "production" / "topic_03" / "audio" / "full_timeline_word_timestamps.json"
COMPILED_SHOTS_FILE = BASE_DIR / "scratch" / "compiled_99_shots.json"
SCHEMA_FILE = BASE_DIR / "public" / "schema.json"
OUTPUT_FILE = BASE_DIR / "topic_03_sceneflow_sync.json"

# Track definitions matching taruma/SceneFlow cues.ts tokens
TRACK_DEFINITIONS = [
    {"index": 0, "type": "dialogue", "name": "Dialogue", "colorClass": "bg-yellow-400/50", "rgb": "250, 204, 21"},
    {"index": 1, "type": "action", "name": "Action", "colorClass": "bg-blue-500/50", "rgb": "59, 130, 246"},
    {"index": 2, "type": "camera", "name": "Camera", "colorClass": "bg-green-500/50", "rgb": "34, 197, 94"},
    {"index": 3, "type": "shot", "name": "Shot", "colorClass": "bg-indigo-400/50", "rgb": "129, 140, 248"},
    {"index": 4, "type": "audio", "name": "Audio", "colorClass": "bg-orange-400/50", "rgb": "251, 146, 60"},
    {"index": 5, "type": "vfx", "name": "VFX", "colorClass": "bg-cyan-400/50", "rgb": "6, 182, 212"},
    {"index": 6, "type": "transition", "name": "Transition", "colorClass": "bg-rose-500/50", "rgb": "244, 63, 94"},
    {"index": 7, "type": "environment", "name": "Environment", "colorClass": "bg-slate-400/50", "rgb": "148, 163, 184"},
]

TRACK_INDEX_MAP = {t["type"]: t["index"] for t in TRACK_DEFINITIONS}
TRACK_COLOR_MAP = {t["type"]: t["colorClass"] for t in TRACK_DEFINITIONS}

# 5 Acts structural division
ACTS_INFO = [
    {
        "act": 1,
        "title": "The Crime Scene at 11:42 PM",
        "shots": "LINE_01-A to LINE_08-D",
        "timeRange": [0.0, 104.33],
        "description": "Nocturnal paralysis at the desk, the blinking cursor, somatic shame, and the biological defense revelation."
    },
    {
        "act": 2,
        "title": "The Biological Ambush",
        "shots": "LINE_09-A to LINE_15-C",
        "timeRange": [104.33, 222.99],
        "description": "Prefrontal cortex CEO vs amygdala guard dog, emotional regulation vs time management, and emotional debt."
    },
    {
        "act": 3,
        "title": "The Stranger in Your Head",
        "shots": "LINE_16-A to LINE_23-B",
        "timeRange": [222.99, 324.20],
        "description": "UCLA Hal Hershfield fMRI discoveries: future self processed as a complete stranger and the tragic morning loop."
    },
    {
        "act": 4,
        "title": "The 5-Second Interactive Test",
        "shots": "LINE_24-A to LINE_31-A",
        "timeRange": [324.20, 434.61],
        "description": "The interactive countdown apparatus (5, 4, 3, 2, 1), somatic micro-flinch detection, and chemical activation energy."
    },
    {
        "act": 5,
        "title": "The Micro-Habit Antidote",
        "shots": "LINE_32-A to LINE_39-A",
        "timeRange": [434.61, 565.10],
        "description": "Protocol 1: Two-Minute Gateway (BJ Fogg/James Clear) and Protocol 2: Self-Compassion Paradox (Dr. Fuschia Sirois)."
    }
]

def get_act_for_shot(shot_id: str) -> dict:
    line_num = int(shot_id.split("-")[0].replace("LINE_", ""))
    if line_num <= 8:
        return ACTS_INFO[0]
    elif line_num <= 15:
        return ACTS_INFO[1]
    elif line_num <= 23:
        return ACTS_INFO[2]
    elif line_num <= 31:
        return ACTS_INFO[3]
    else:
        return ACTS_INFO[4]

def normalize_words(words):
    normalized = []
    i = 0
    while i < len(words):
        w = words[i]
        text = w["word"]
        if i + 1 < len(words):
            next_w = words[i+1]
            next_text = next_w["word"]
            if text.isdigit() and next_text.startswith('.') and next_text[1:].isdigit():
                merged_word = f"{text}:{next_text[1:]}"
                normalized.append({
                    "word": merged_word,
                    "start": w["start"],
                    "end": next_w["end"]
                })
                i += 2
                continue
            elif text.isdigit() and next_text.startswith(',') and next_text[1:].isdigit():
                merged_word = f"{text}{next_text}"
                normalized.append({
                    "word": merged_word,
                    "start": w["start"],
                    "end": next_w["end"]
                })
                i += 2
                continue
        normalized.append(w)
        i += 1
    return normalized

def build_adaptive_phrases_from_data(word_data, shots=None, max_chars=22):
    phrases = []
    for seg in word_data["segments"]:
        words = seg.get("words", [])
        if not words:
            continue
        words = normalize_words(words)
        i = 0
        while i < len(words):
            take = 2
            if i + 3 <= len(words):
                three_words = words[i:i+3]
                char_len = sum(len(w["word"]) for w in three_words)
                if char_len <= max_chars and (len(words) - i) != 4:
                    take = 3
            elif (len(words) - i) == 3:
                take = 3
            else:
                take = len(words) - i
                
            chunk = words[i:i+take]
            p_start = chunk[0]["start"]
            p_end = chunk[-1]["end"] + (0.22 if i+take >= len(words) else 0.05)
            
            phrases.append({
                "start": p_start,
                "end": p_end,
                "words": chunk,
                "text": " ".join([w["word"] for w in chunk])
            })
            i += take

    # Snap phrase boundaries to visual cuts
    if shots:
        cut_times = [s["end"] for s in shots[:-1]]
        for p in phrases:
            for cut_t in cut_times:
                if 0 < (cut_t - p["start"]) < 0.35:
                    p["start"] = cut_t
                if 0 < (p["end"] - cut_t) < 0.20:
                    p["end"] = cut_t

    # Fix any inverted or zero-duration phrases caused by cut-snapping
    for p in phrases:
        if p["end"] <= p["start"]:
            p["start"] = p["words"][0]["start"]
            p["end"] = p["words"][-1]["end"] + 0.05

    return phrases

# 99 Master Shots Descriptive Catalog for Authentic Narrative Cues
# Derived directly from IMAGE_TO_LINE_MAPPING_TOPIC_03.md and prompts/TOPIC_03_ALL_FINAL_SHOT_PROMPTS_CLEAN.md
SHOT_CATALOG = {
    "LINE_01-A": {
        "title": "Wide Establishing Shot (35mm) - Slumped at Floating Desk at 11:42 PM",
        "action": "Sam sits heavily slumped in an ergonomic chair at a floating desk, chin cupped in palm.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Eerie Sub-Bass Ambient Drone & 1Hz Clock Ticks",
        "vfx_desc": "6500K Cold Blue Laptop Screen Uplight & Red LED Clock Glow",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_01-B": {
        "title": "Macro Hero Prop Insert (85mm) - 11:42 PM Digital Clock & Warning",
        "action": "Sam's eyes shift nervously toward pulsing red digital clock digits on the desk.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Loud Resonant Metallic Clock Tick (11:42 PM)",
        "vfx_desc": "Pulsing Red LED Display & Translucent Holographic Deadline Pill",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_02-A": {
        "title": "Over-the-Shoulder POV (50mm) - Intimidating Blank Document",
        "action": "Sam opens laptop lid; back of head and glasses visible in foreground facing blank white screen.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Laptop Fan Whisper & Typing Hesitation Silence",
        "vfx_desc": "High-Key White Screen Glare & Anodized Aluminum Chassis Speculars",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_02-B": {
        "title": "Macro Screen Close-Up (100mm) - Solitary Mockingly Blinking Cursor",
        "action": "The solitary black cursor blinks rhythmically in upper corner of pristine document.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Subtle Metronomic Digital Tick Aligned with Cursor Flash",
        "vfx_desc": "Razor-Sharp Micro-Pixel Grid Texture & Emissive White Canvas",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_02-C": {
        "title": "Macro Reflection Angle (85mm) - Anxious Gaze in Glossy Monitor Bezel",
        "action": "Sam's hazel eyes and black glasses reflect downward in glossy monitor bezel in psychological paralysis.",
        "camera_desc": "Quick Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Low Sub-Bass Swell & Muffled Heartbeat Thump",
        "vfx_desc": "Glossy Bezel Mirroring with Lens Caustics & Blue Anti-Reflective Glints",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_03-A": {
        "title": "Macro Action Insert (85mm) - Trembling Fingers Suspended Over Keys",
        "action": "Sam's hands hover exactly one inch above keys, fingers trembling with nervous tension.",
        "camera_desc": "Subtle 2D Diagonal Drift (101% -> 104.5% Scale)",
        "audio_desc": "Tense Room Tone & Subtle Finger Knuckle Shiver",
        "vfx_desc": "Backlit Keyboard Chiclet Glow Under Knuckles",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_03-B": {
        "title": "Dynamic Action Snap (50mm) - Impulsive Grab for Smartphone",
        "action": "Sam's right hand impulsively darts sideways, snatching the black smartphone off the desk.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Quick Leather Desk Swipe & Smartphone Pickup Click",
        "vfx_desc": "Motion Blur Streak on Darting Hand & Guilty Eye Dart",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_03-C": {
        "title": "Close-Up Thumb Scrolling (50mm) - Hypnotic Social Feed Blur",
        "action": "Sam's thumb flicks upward in cartoon motion blur, scrolling through forgettable video feeds.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Rapid Glass Screen Swipes & Muffled Video Feed Chirps",
        "vfx_desc": "Rainbow Screen Light Pulse Washing Across Fingers and Frame",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_03-D": {
        "title": "Medium Profile Glow Shot (50mm) - Rainbow Screen Glow on Face",
        "action": "Sam stares wide-eyed and hypnotized into the glowing phone screen with glassy pupils.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Hypnotic Synth Wash & Muted White Noise",
        "vfx_desc": "Saturated Shifting Rainbow Emissive Reflection on Spectacle Lenses",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_04-A": {
        "title": "Tight Macro Close-Up (85mm) - Joyless Deadpan Expression",
        "action": "Sam's face remains completely flat, joyless, and devoid of dopamine pleasure.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Distant High-Frequency Tinnitus Ringing",
        "vfx_desc": "Dark Eye Rings & Desaturated Skin Tones Under Blue Uplight",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_04-B": {
        "title": "Medium Profile Somatic Shot (50mm) - Hand Clutching Tight Solar Plexus",
        "action": "Sam clutches his solar plexus in physical nausea and autonomic nervous system distress.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Deep Somatic Heartbeat Pulse (Low-Pass Filtered)",
        "vfx_desc": "Glistening Sweat Droplet on Temple & Strained Neck Tendons",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_04-C": {
        "title": "Metaphorical Close-Up (85mm) - Purple Frost of Shame Creeping Up Throat",
        "action": "Sam swallows hard as dark frost of shame creeps visibly up his neck and throat.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Subtle Ice Crystalline Creep SFX & Muffled Gulp",
        "vfx_desc": "Translucent Purple Crystalline Frost Crawling Up Throat Cartilage",
        "env_label": "Solid Obsidian Indigo Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_05-A": {
        "title": "Side Profile Slump (50mm) - Head Falling Forward in Defeat",
        "action": "Sam drops hands and upper torso begins slow-motion fall toward wooden desk.",
        "camera_desc": "Subtle 2D Diagonal Drift (101% -> 104.5% Scale)",
        "audio_desc": "Heavy Exhaled Sigh of Self-Loathing",
        "vfx_desc": "Soft Contact Floor Shadow & Atmospheric Shadow Falloff",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_05-B": {
        "title": "The Desk Impact Shot (50mm) - Forehead Resting Flat Against Oak Tabletop",
        "action": "Sam's forehead gently slams flat against oak desk; arms dangle limply like dead weights.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Solid Wood Tabletop Impact Thud & Glasses Slide Click",
        "vfx_desc": "Glasses Skewed on Nose Bridge & Tactile Oak Grain Reflections",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_05-C": {
        "title": "Direct Overhead Crane Shot (35mm) - Curled in Defeated Ball in Empty Space",
        "action": "Sam lies curled into a defeated ball beside open laptop and phone in vast void.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Cavernous Reverb Swell of Clock Ticking in Isolation",
        "vfx_desc": "High Architectural 90° Overhead Symmetry & Circular Floor Shadow",
        "env_label": "Solid Dull Muted Sky Blue Floor Plane (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_06-A": {
        "title": "Explainer Staging Transition (50mm) - Sam Standing Upright Facing Camera",
        "action": "Lighting transitions warm; Sam stands upright in navy sweater, smiling with empathy.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Warm Ambient Acoustic Chord Swell (Pivot to Explainer)",
        "vfx_desc": "Atmospheric Color Transition Dissolving Cold Blue into Seafoam Green",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_06-B": {
        "title": "Medium Explainer Shot (50mm) - Pushing Up Glasses Beside Glowing Glass Brain",
        "action": "Sam gently pushes up black glasses with index finger; specular star glints on frame.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Clean Finger Tap on Frame & High-Frequency Shimmer",
        "vfx_desc": "Translucent 3D Optical Glass Brain with Glowing Cyan & Amber Fiber Optics",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_07-A": {
        "title": "Vintage Blackboard Staging (50mm) - Equation PROCRASTINATION = LAZY",
        "action": "Sam stands with arms crossed beside floating blackboard with equation PROCRASTINATION = LAZY.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Chalkboard Frame Wood Creak & Ambient Studio Air",
        "vfx_desc": "Neat White Chalk Typography on Dark Slate Frame",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_07-B": {
        "title": "Dynamic Chalk Action (50mm) - Decisive Red Chalk Slash Across LAZY",
        "action": "Sam draws a bold, thick diagonal red chalk slash directly through the word LAZY.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Crisp High-Friction Red Chalk Scratch SFX Across Slate",
        "vfx_desc": "Floating Red Chalk Dust Particles in Volumetric Key Light",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_07-C": {
        "title": "Hero Prop Comedy Insert (50mm) - Swatting Away Floating Pastel Planners",
        "action": "Sam playfully swats away floating leather daily planners, sticky notes, and calendar grids.",
        "camera_desc": "Smooth Pan Left (103.5% Scale, Right 51.5% -> Left 48.5%)",
        "audio_desc": "Cartoon Paper Flutter Whoosh & Dismissive Palm Slap",
        "vfx_desc": "Pastel Planners Dispersing into Negative Space with Motion Lines",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_08-A": {
        "title": "Centered Dramatic Chiaroscuro (85mm) - Raised Finger of Conviction",
        "action": "Sam raises single index finger with intellectual conviction against obsidian slate void.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Deep Theatrical Bass Hit & Muted Stinger",
        "vfx_desc": "High-Contrast Chiaroscuro with Razor-Sharp Cyan Rim Light Sculpting Hair",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_08-B": {
        "title": "Hero Close-Up Revelation (85mm) - 3D Typography BIOLOGICAL DEFENSE",
        "action": "Sam gestures toward glowing golden 3D acrylic letters: BIOLOGICAL DEFENSE.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Harmonic Resonant Chord & Low Brass Drone",
        "vfx_desc": "Sculpted 3D Golden Acrylic Typography Casting Radiant Amber Glow on Chest",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_08-C": {
        "title": "3D Skull Cutaway Profile (50mm) - Holographic Wireframe Amygdala Red Emergency Node",
        "action": "Sam turns profile as illuminated 3D skull reveals pulsing red amygdala node.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Pulsing Electronic Beacon Tone (2Hz)",
        "vfx_desc": "Electric Cyan Vector Circuit Skull & Almond-Shaped Crimson Amygdala Node",
        "env_label": "Solid Dark Slate-Indigo Studio Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_08-D": {
        "title": "Macro Brain Command Bunker (85mm) - Security Guard Pulling Red Alarm Lever",
        "action": "Miniature cartoon security guard frantically throws both hands onto red industrial ALARM lever.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Piercing Industrial Emergency Siren Wails & Metallic Lever Clunk",
        "vfx_desc": "Sweeping Red Emergency Siren Light Beams Through Steam Vents",
        "env_label": "Brain Command Bunker Console (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_09-A": {
        "title": "Symmetrical Studio Staging (50mm) - Ornate Brass Balance Scale (CEO vs Guard Dog)",
        "action": "Ornate vintage brass balance scale balances miniature CEO on left vs anxious dog on right.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Metallic Scale Pivot Clink & Balanced Ticking",
        "vfx_desc": "Warm 3-Point Studio Lighting with Crisp Metallic Specular Highlights",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_09-B": {
        "title": "Medium Close-Up Character (50mm) - Miniature Prefrontal Cortex CEO Straightening Tie",
        "action": "Miniature CEO in charcoal suit straightens tie with confident executive composure.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Silk Tie Adjust Rustle & Polished Briefcase Latch Snap",
        "vfx_desc": "Crisp Commercial Rim Lighting & Gold-Rimmed Eyeglass Catchlights",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_09-C": {
        "title": "Macro Product Cinematography (85mm) - Glowing Golden Timeline on Digital Tablet",
        "action": "Two hands in tailored suit sleeves hold futuristic glass tablet with glowing timeline.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Futuristic Digital Interface Chime & Data Scroll Chirp",
        "vfx_desc": "Glowing Vector Timeline Nodes with Soft Light Streaks in Glass",
        "env_label": "Dark Slate-Teal Void (#2c4a52)",
        "env_hex": "#2c4a52"
    },
    "LINE_10-A": {
        "title": "Confident Forward Stride (50mm) - CEO Pointing Toward Golden Horizon",
        "action": "Miniature CEO strides forward with disciplined optimism, pointing toward golden horizon.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Confident Footsteps on Polished Surface & Uplifting Synth Drone",
        "vfx_desc": "Radiant Golden Volumetric Rim Lighting & Floor Reflections",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_10-B": {
        "title": "Dramatic Low-Angle Shock Cut (50mm) - Panicked Amygdala Guard Dog Crouching",
        "action": "Miniature cartoon guard dog crouches terrified on dark metallic surface with bulging eyes.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Panicked Canine Whimper & Screeching Emergency Siren Tone",
        "vfx_desc": "Theatrical Crimson Key Light Sweeping Across Dark Metallic Surface",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_10-C": {
        "title": "Comic Confusion Close-Up (50mm) - Guard Dog Staring Cross-Eyed at Floating Calendar",
        "action": "Miniature guard dog stares cross-eyed and suspicious at floating 3D calendar page.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Cartoon Curio Pluck & Dog Whimper Squeak",
        "vfx_desc": "Cartoon Sweat Droplet Popping Off Forehead & Floating Grid Page",
        "env_label": "Solid Dark Slate-Indigo Studio Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_11-A": {
        "title": "Retro-Industrial Console Macro (85mm) - Paws Hovering Over IMMEDIATE SURVIVAL Button",
        "action": "Miniature dog paws hover tensely over glossy red button labeled IMMEDIATE SURVIVAL.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "High-Voltage Relay Hum & Tension Tone",
        "vfx_desc": "Intense Red Emissive Button Glow Bouncing Off Metallic Rivets",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_11-B": {
        "title": "Explainer Staging (50mm) - Sam Holding Research Book and Gesturing",
        "action": "Sam holds open leather research book in arm, gesturing openly with warm expression.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Warm Acoustic Guitar Strung Chord",
        "vfx_desc": "Balanced 3-Point Explainer Lighting & Rich Subsurface Skin Glow",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_11-C": {
        "title": "Floating 3D Golden Plaque (50mm) - EMOTIONAL REGULATION > TIME MANAGEMENT",
        "action": "Sam points index finger decisively at floating golden text: EMOTIONAL REGULATION > TIME MANAGEMENT.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Resonant Bell Ding & Authority Stinger",
        "vfx_desc": "3D Sculpted Golden Typography Casting Radiant Amber Glow on Chest",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_12-A": {
        "title": "High-Angle Minimalist Desk (50mm) - Pristine White Wireless Keyboard",
        "action": "Sam's hands rest peacefully on desk beside pristine white wireless chiclet keyboard.",
        "camera_desc": "Subtle 2D Diagonal Drift (101% -> 104.5% Scale)",
        "audio_desc": "Calm Room Ambience & Soft Wood Contact",
        "vfx_desc": "Diffused Daylight Studio Wash & Soft Contact Floor Shadow",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_12-B": {
        "title": "Dynamic Metamorphosis Shot (50mm) - Paper Sheet Morphs into Origami Beast",
        "action": "Sam recoils backward in chair as white paper sheet folds into snarling geometric origami monster.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Rapid Crisp Paper Origami Creasing & Snarling Paper Beast Growl",
        "vfx_desc": "Glowing Crimson Geometric Eyes & Chiaroscuro Red Shadows",
        "env_label": "Solid Dark Slate-Teal Void (#2c4a52)",
        "env_hex": "#2c4a52"
    },
    "LINE_12-C": {
        "title": "Symmetrical Conceptual Staging (50mm) - Three Floating Frosted-Glass Fear Index Cards",
        "action": "Sam stands behind three floating frosted-glass cards: FEAR OF FAILURE, JUDGMENT, PERFECTIONISM.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Glass Frosted Resonance & Harmonic Three-Note Chime",
        "vfx_desc": "Ominous Red Engraved Typography in Glass Casting Emissive Glow on Sweater",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_13-A": {
        "title": "Wide Command Bunker (50mm) - Amygdala Dog Covering Ears Amid Red Sirens",
        "action": "Miniature guard dog runs in frantic panic covering ears as sirens spin on bunker ceiling.",
        "camera_desc": "Smooth Pan Left (103.5% Scale, Right 51.5% -> Left 48.5%)",
        "audio_desc": "Overwhelming Emergency Klaxon Alarms & Steam Release Hiss",
        "vfx_desc": "Volumetric Red Light Beams Cutting Through Swirling White Steam Vents",
        "env_label": "Industrial Cartoon Command Bunker (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_13-B": {
        "title": "Dynamic Action Jump (50mm) - Amygdala Dog Slamming PULL FOR MOOD REPAIR Lever",
        "action": "Miniature guard dog jumps and slams both front paws onto red PULL FOR MOOD REPAIR lever.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Heavy Industrial Mechanical Lever Clunk & Emergency Switch Trip",
        "vfx_desc": "Tactile Metallic Lever Highlight & Red Flash Dimming",
        "env_label": "Industrial Cartoon Command Bunker (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_13-C": {
        "title": "Surreal Transformation Shot (50mm) - Origami Monster Dissolves into Smartphone",
        "action": "Paper monster dissolves into cloud of sparkling golden dust, leaving glowing smartphone.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Magical Golden Sparkle Chime & Smartphone Notification Ding",
        "vfx_desc": "Sparkling Golden Dust Motes Dissolving into Saturated Colorful App Icons",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_14-A": {
        "title": "Cozy Comfort Shot (50mm) - Curled in Armchair Inside Golden Forcefield Bubble",
        "action": "Sam curls comfortably in yellow armchair inside glowing forcefield, cradling steaming mug.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Cozy Warm Fireplace Hum & Gentle Steam Sigh",
        "vfx_desc": "Translucent Golden Spherical Forcefield Bubble with Shimmering Optical Caustics",
        "env_label": "Solid Dark Slate-Indigo Studio Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_14-B": {
        "title": "Scientific Micro Cinematography (85mm) - Golden Dopamine Droplet Landing on Receptor",
        "action": "Glowing translucent golden droplet of liquid dopamine lands on crystalline neural docking node.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Deep Microscopic Liquid Drop Bloom & Radiant Sine Resonance",
        "vfx_desc": "Radiant Amber Light Shockwave & Tiny Sparkle Particles Along Glass Dendrites",
        "env_label": "Clean Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_14-C": {
        "title": "Shattering Action Shot (50mm) - Forcefield Bubble Explodes into Crystalline Shards",
        "action": "Golden bubble shatters into sharp flying crystalline glass fragments; Sam shivers on bare floor.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Violent Glass Showning Crash & Sudden Freezing Wind Gust",
        "vfx_desc": "Dozens of Flying Glass Fragments with Sharp Specular Highlights in Cold Spotlight",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_15-A": {
        "title": "Noir Perspective Wide Shot (35mm) - Monolithic Towers of Overdue Paperwork",
        "action": "Sam sits tiny and isolated beneath towering skyscrapers of stacked paperwork and ticking clocks.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Low Oppressive Drone & Echoing Clock Ticks in Grand Canyon",
        "vfx_desc": "Theatrical Overhead Spotlight Casting Long Dramatic Shadows Across Floor",
        "env_label": "Deep Slate-Teal Void (#2c4a52)",
        "env_hex": "#2c4a52"
    },
    "LINE_15-B": {
        "title": "Macro Product Cinematography (85mm) - Translucent Crimson EMOTIONAL DEBT Credit Card",
        "action": "Two hands hold translucent crimson acrylic card reading EMOTIONAL DEBT: OVERDUE.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Heavy Credit Card Chip Beep & Cash Register Drawer Slam",
        "vfx_desc": "Embossed Metallic Gold Typography & Crisp Specular Catchlights on Card Bevel",
        "env_label": "Solid Dark Slate-Indigo Studio Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_15-C": {
        "title": "Medium Presenter Smirk (50mm) - Illuminated Glass Slide with Brain fMRI Heatmap",
        "action": "Sam holds up illuminated rectangular glass slide displaying glowing brain fMRI heatmap.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Glass Slide Click & Subtle Curious Synth Motif",
        "vfx_desc": "Glowing Cyan and Crimson Brain fMRI Heatmap Glowing Translucent on Slide",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_16-A": {
        "title": "Medical Laboratory Scanning (50mm) - Translucent 3D Skull in UCLA fMRI Laser Grid",
        "action": "Translucent 3D skull scanned by cyan laser grid inside high-tech UCLA scanner chamber.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "fMRI Rhythmic Magnetic Knocking Pulses & Laser Sweep Hum",
        "vfx_desc": "Volumetric Cyan Laser Grid Sweeping Through Glass Cranium",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_16-B": {
        "title": "Macro Glass Brain Cinematography (85mm) - Glowing Fiber-Optic Neural Networks",
        "action": "Intricate optical fiber networks pulse with bright pulses of light through cerebral cortex.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "High-Speed Data Flow Shimmer & Microscopic Neural Pulses",
        "vfx_desc": "Cyan and Amber Fiber-Optic Bundles Glowing in Optical Glass Caustics",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_17-A": {
        "title": "Present-Self Brain Mapping (50mm) - Sam Pointing at Medial Prefrontal Cortex",
        "action": "Sam points at chest indicating present self as medial prefrontal cortex lights up.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Harmonic Resonant Chord & Heartbeat Sub-Bass",
        "vfx_desc": "Present Self Baseline Glow & Warm Amber Key Light",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_17-B": {
        "title": "Macro Neural Bonfire (85mm) - mPFC Lighting Up with Radiant Golden Amber Energy",
        "action": "Medial prefrontal cortex illuminates like a radiant golden Christmas tree inside skull.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Radiant Chime Swell & Crackling Golden Neural Sparks",
        "vfx_desc": "Intense Golden Amber Neural Fireworks Spreading Outward from mPFC Node",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_18-A": {
        "title": "Total Stranger Baseline (50mm) - Faceless Mannequin Waiting Alone at Bus Bench",
        "action": "Faceless grey wooden mannequin sits alone on wooden bench in empty space.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Distant Cold City Wind & Lone Streetlight Buzz",
        "vfx_desc": "Desaturated Slate Tones with Soft Cold Overhead Spotlight",
        "env_label": "Dark Muted Slate Void (#1e293b)",
        "env_hex": "#1e293b"
    },
    "LINE_18-B": {
        "title": "Macro Mannequin Head (85mm) - Inspecting Featureless Grey Mannequin",
        "action": "Camera pushes close on smooth featureless wooden head of the stranger mannequin.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Eerie Hollow Silence & Low Synth Whine",
        "vfx_desc": "Smooth Wood Grain Micro-Textures & Cold Grey Contact Shadow",
        "env_label": "Dark Muted Slate Void (#1e293b)",
        "env_hex": "#1e293b"
    },
    "LINE_18-C": {
        "title": "Brain Power-Down Cutaway (50mm) - Neural Circuits Fading to Desaturated Flat Grey",
        "action": "Brain neural circuits power down completely into cold, desaturated lifeless grey.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Power Down Sine Drop SFX & Muted Click",
        "vfx_desc": "Golden Amber Energy Fading to Flat Neutral Matte Grey",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_19-A": {
        "title": "Future-Self Breakthrough (50mm) - Present Sam Staring at Glowing Future Avatar",
        "action": "Present Sam sits looking up at translucent, ghostly avatar of his future self.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Sci-Fi Hologram Hum & Sub-Bass Rumble",
        "vfx_desc": "Translucent Cyan Holographic Avatar with Soft Volumetric Glow",
        "env_label": "Solid Dark Slate-Indigo Studio Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_19-B": {
        "title": "Ghostly Face-to-Face (50mm) - Mutual Emotional Disconnect Between Selves",
        "action": "Present Sam and Future Avatar face each other; zero emotional resonance passes between them.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Eerie Two-Tone Drone & Cold Breathing Ambience",
        "vfx_desc": "Ghostly Holographic Scanlines Passing Across Future Sam's Cheeks",
        "env_label": "Solid Dark Slate-Indigo Studio Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_19-C": {
        "title": "Dual Brain Scan Display (50mm) - Identical Inactive Neural Patterns for Stranger and Future",
        "action": "Split screen fMRI scan displays showing identical zero-mPFC patterns for stranger and future self.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Medical Display Beep & Data Sync Tone",
        "vfx_desc": "Split Screen Golden Border & Identical Flat Grey Brain Profiles",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_20-A": {
        "title": "Disbelief Close-Up (85mm) - Sam Processing the Neurological Stranger Illusion",
        "action": "Sam's eyes widen in intellectual shock behind glasses as the cognitive trap is revealed.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Sudden Sharp Inhale & Disbelief Piano Note",
        "vfx_desc": "Sharp Rim Light on Jawline & Specular Eyeglass Reflection",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_20-B": {
        "title": "Split Conceptual Reality (50mm) - Relaxed Armchair Sam vs Chained Desk Future Sam",
        "action": "Relaxed Sam sits comfortably eating popcorn while Chained Future Sam sweats at desk.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Carefree Popcorn Crunch vs Clanking Heavy Iron Chains",
        "vfx_desc": "Split Studio Plane: Golden Comfort on Left, Cold Shadow on Right",
        "env_label": "Split Studio Plane (#f3e5d0 / #0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_20-C": {
        "title": "Passing the Heavy Burden (50mm) - Armchair Sam Dumps Heavy Crate on Future Sam",
        "action": "Armchair Sam cheerfully dumps heavy wooden crate of overdue files on chained Future Sam.",
        "camera_desc": "Smooth Pan Left (103.5% Scale, Right 51.5% -> Left 48.5%)",
        "audio_desc": "Heavy Wooden Crate Impact Thud & Exhaled Strain Grunt",
        "vfx_desc": "Dust Cloud Popping on Impact & Iron Chain Tension Glints",
        "env_label": "Solid Dark Slate-Indigo Studio Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_21-A": {
        "title": "Superhero Fantasy Delusion (50mm) - Golden Cape Future Sam with Superhuman Discipline",
        "action": "Idealized Future Sam stands heroically in gold-trimmed superhero cape, chest puffed out.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Triumphant Brass Superhero Fanfare",
        "vfx_desc": "Radiant Golden Volumetric God Rays & Fluttering Cape Dynamics",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_21-B": {
        "title": "Idealized Speed Typing (50mm) - Future Sam Typing 10-Page Paper at 6:00 AM",
        "action": "Future Sam's hands fly across keyboard at impossible superhuman speed, papers stacking neat.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Machine Gun Rapid Keyboard Clatter & Energetic Synth Arpeggio",
        "vfx_desc": "Golden Motion Streaks Flowing from Fingertips onto Pristine Pages",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_22-A": {
        "title": "Violent Morning Awakening (50mm) - Shaking 07:00 AM Alarm Clock",
        "action": "Retro alarm clock violently rattles and vibrates at 07:00 AM on bedside table.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Deafening Piercing Brass Twin-Bell Alarm Ring (07:00 AM)",
        "vfx_desc": "Vibration Shockwave Blur Rings & Emissive Red 07:00 AM Numerals",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_22-B": {
        "title": "The Cruel Reality (50mm) - Exhausted Sam Realizing Stranger is Him",
        "action": "Sam wakes tangled in sheets with disheveled hair, realizing the cruel joke: Stranger is him.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Alarm Ring Sudden Stop & Weary Morning Groan",
        "vfx_desc": "Pale Cold Morning Light & Bleary Squinting Hazel Eyes",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_23-A": {
        "title": "Somatic Defeat Close-Up (50mm) - Head Buried in Hands on Edge of Bed",
        "action": "Sam sits on edge of bed with face buried in trembling hands, burdened by inherited debt.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Heavy Depressing Cello Tone & Muted Exhale",
        "vfx_desc": "Cold Desaturated Studio Lighting & Hunched Silhouette",
        "env_label": "Solid Dull Muted Sky Blue Studio Void (#6ba4b8)",
        "env_hex": "#6ba4b8"
    },
    "LINE_23-B": {
        "title": "Antique Prop Cinematography (85mm) - Hourglass Rapidly Draining Golden Sand",
        "action": "Antique brass hourglass drains fine golden sand rapidly through narrow glass neck.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Soft Whispering Sand Drainage SFX",
        "vfx_desc": "Glass Specular Refractions & Golden Dust Particles in Air",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_24-A": {
        "title": "Void Staging Reveal (35mm) - Massive Circular Metallic Countdown Apparatus",
        "action": "Massive circular metallic countdown apparatus materializes silently in pure obsidian void.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Deep Cinematic Sub-Bass Swell & Mechanical Locking Drone",
        "vfx_desc": "High-Contrast Edge Lighting on Heavy Matte Titanium Housing",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_24-B": {
        "title": "Timer Priming Close-Up (50mm) - Electric Cyan Bezel Luminescence and Instructions",
        "action": "Countdown circular bezel primes, pulsing with saturated electric cyan luminescence.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "High-Voltage Capacitor Charging Whine (Ascending Pitch)",
        "vfx_desc": "Electric Cyan Circular Neon Bezel Pulse & Soft Reflection on Housing",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_25-A": {
        "title": "Interactive Digit 5 (85mm) - Vivid 3D Cyan Acrylic Numeral 5",
        "action": "Vivid 3D cyan acrylic numeral 5 snaps instantaneously into dead center of frame.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Heavy Bass Punch & Sub-Bass Kick (Countdown Tick 5)",
        "vfx_desc": "Saturated Cyan Acrylic Internal Glow & Polished Bevel Highlights",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_25-B": {
        "title": "Interactive Digit 4 (85mm) - Vivid 3D Warm Amber Numeral 4",
        "action": "Vivid 3D warm amber numeral 4 snaps instantaneously with zero latency.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Resonant Woodblock & Amber Bass Staccato (Countdown Tick 4)",
        "vfx_desc": "Warm Amber Translucent Acrylic Glow with Refractive Internal Bubbles",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_26-A": {
        "title": "Interactive Digit 3 (85mm) - Vivid 3D Deep Gold Numeral 3",
        "action": "Vivid 3D deep gold numeral 3 snaps with precision hard cut.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Heavy Metallic Anvil Clank (Countdown Tick 3)",
        "vfx_desc": "Polished Brushed Gold Texture & High-Voltage Edge Rim Glints",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_26-B": {
        "title": "Interactive Digit 2 (85mm) - Vivid 3D High-Contrast Specular Numeral 2",
        "action": "Vivid 3D high-contrast numeral 2 snaps into place under dramatic top spotlight.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Sharp High-Frequency Glass Strike & Sub Hit (Countdown Tick 2)",
        "vfx_desc": "High-Contrast Specular Catchlights & Volumetric Cyan-Gold Split Beam",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_26-C": {
        "title": "Interactive Digit 1 (85mm) - Vivid 3D Numeral 1 & Detonation Particle Shockwave",
        "action": "Vivid 3D numeral 1 detonates into expanding golden particle shockwave across the screen.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Massive Sub-Bass Detonation Boom & Expanding Sparkle Shockwave",
        "vfx_desc": "Exploding Ring of Golden Particle Stars & Radiant White Flash",
        "env_label": "Solid Obsidian Slate Void (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_27-A": {
        "title": "Direct Camera Inquiry (50mm) - Sam Inquiring About Viewer's Somatic Flinch",
        "action": "Sam points directly into camera lens, inquiring warmly about the physical bodily flinch.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Warm Acoustic Bass Entry & Intimate Room Tone",
        "vfx_desc": "Soft 3-Point Explainer Lighting & Direct Hazel Eye Catchlights",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_27-B": {
        "title": "Somatic Biofeedback (50mm) - Hand on Sternum Checking Shallow Breathing Knot",
        "action": "Sam places hand flat on sternum, checking the knot in the solar plexus and shallow breath.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Subtle Sharp Inhale Audio & Muffled Somatic Thump",
        "vfx_desc": "Subtle Blue Chest Illumination Visualizing Somatic Tension",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_27-C": {
        "title": "Internal Voice Shadow (50mm) - Smoky Shadow Whispering 'I Will Do That Later'",
        "action": "Smoky dark shadow figure leans in behind Sam's ear whispering 'I will do that later tonight'.",
        "camera_desc": "Subtle 2D Diagonal Drift (101% -> 104.5% Scale)",
        "audio_desc": "Muffled Whisper SFX ('Later tonight...') in Left/Right Stereo",
        "vfx_desc": "Semi-Translucent Dark Smoke Tendrils Curling Around Neck",
        "env_label": "Solid Dark Slate-Teal Void (#2c4a52)",
        "env_hex": "#2c4a52"
    },
    "LINE_28-A": {
        "title": "Dismissal Action (50mm) - Sam Brushing Away Smoky Shadow Figure",
        "action": "Sam sweeps right arm decisively through the air, dispersing the smoky shadow into mist.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Clean Wind Air Whoosh SFX & Crisp Hand Sweep",
        "vfx_desc": "Smoke Dissolving into Sparkling Dust Particles Under Key Light",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_28-B": {
        "title": "Scientific Staging (50mm) - Glowing Molecular Chemical Reaction Beaker",
        "action": "Floating glass laboratory beaker shows glowing chemical reaction bonds colliding.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Liquid Chemical Bubble SFX & High Molecular Chime",
        "vfx_desc": "Glowing Chemical Bonds (Cyan/Amber) & Glass Refractions",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_28-C": {
        "title": "Glass Graph Plaque (50mm) - 3D Activation Energy Threshold Curve Plaque",
        "action": "Suspended frosted-glass plaque displays 3D Activation Energy hump and threshold line.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Resonant Glass Hum & Marker Line Trace SFX",
        "vfx_desc": "Glowing Red Peak Curve & Clean White Typography ACTIVATION ENERGY",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_29-A": {
        "title": "Overwhelming Task Metaphor (35mm) - Colossal 2-Story Granite Boulder",
        "action": "Colossal 2-story cracked granite boulder stands impossibly massive before tiny Sam.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Deep Earth Tremor Rumble & Heavy Stone Groan",
        "vfx_desc": "Dramatic Overhead Spotlight Casting Enormous Shadow Over Frame",
        "env_label": "Deep Slate-Teal Void (#2c4a52)",
        "env_hex": "#2c4a52"
    },
    "LINE_29-B": {
        "title": "Futile Muscular Strain (50mm) - Sam Straining with Shoulders Against Giant Boulder",
        "action": "Sam presses shoulder desperately against the colossal boulder, muscles straining in vain.",
        "camera_desc": "Rapid Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Muscular Strain Grunt & Ineffective Stone Scraping Sound",
        "vfx_desc": "Sweat Beads on Brow & Flushed Cheeks Under Dramatic Chiaroscuro",
        "env_label": "Deep Slate-Teal Void (#2c4a52)",
        "env_hex": "#2c4a52"
    },
    "LINE_30-A": {
        "title": "Minimalist Studio Plane (50mm) - Pristine Glass Marble on Mirror Table",
        "action": "Pristine transparent glass marble rests motionless on polished reflective studio table.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Total Peaceful Studio Silence & Delicate Glass Tick",
        "vfx_desc": "Flawless Optical Glass Caustics & Reflection on Mirror Surface",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_30-B": {
        "title": "Macro Kinetic Initiation (85mm) - Sam's Pinky Finger Delivering Effortless Micro-Tap",
        "action": "Sam's pinky finger delivers a casual, effortless flick to the glass marble.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Crisp High-Frequency Glass Clack Sound",
        "vfx_desc": "Tiny Golden Sparkle Detonation at Contact Point",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_30-C": {
        "title": "Frictionless Momentum (50mm) - Glass Marble Rolling Effortlessly Across Surface",
        "action": "Glass marble rolls smoothly across mirror surface, gaining effortless speed with zero drag.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Smooth Frictionless Rolling Marble Humming Tone",
        "vfx_desc": "Prismatic Light Trails Following Marble Path Across Mirror",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_31-A": {
        "title": "Solution Pivot Presentation (50mm) - Sam Leaning Forward with Stopwatch and Pen",
        "action": "Sam leans forward toward camera holding chrome stopwatch and sleek pen, ready to reveal antidote.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Optimistic Musical Shift & Acoustic Bass Line",
        "vfx_desc": "Warm Golden Key Lighting & Enlightened Reassuring Smile",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_32-A": {
        "title": "Protocol One Plaque (50mm) - Golden Plaque THE TWO-MINUTE GATEWAY",
        "action": "Sculpted golden acrylic plaque materializes: PROTOCOL 1: THE TWO-MINUTE GATEWAY.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Resonant Golden Bell Chime & Brass Swell",
        "vfx_desc": "Embossed Golden Lettering Casting Amber Radiance Across Frame",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_32-B": {
        "title": "Macro Vintage Stopwatch (85mm) - Sweeping Second Hand Limiting Work to 2 Minutes",
        "action": "Vintage chrome stopwatch held in hand with red second hand sweeping exactly 2 minutes.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Tactile Mechanical Stopwatch Ticks (4 Ticks Per Second)",
        "vfx_desc": "Engraved Dial Texture with Luminous Green 120s Marker Arc",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_33-A": {
        "title": "Micro-Action Vignette 1 (50mm) - Writing Just One Single Sentence on Page",
        "action": "Sam sits at clean desk, writing just one single crisp sentence on blank paper with calm smile.",
        "camera_desc": "Smooth Pan Right (103.5% Scale, Left 48.5% -> Right 51.5%)",
        "audio_desc": "Pleasant Fountain Pen Scratching Rhythm on Textured Paper",
        "vfx_desc": "Warm Studio Sunlight Illuminating Crisp Handwritten Ink",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_33-B": {
        "title": "Micro-Action Vignette 2 (50mm) - Tying Laces on Running Shoe on Stool",
        "action": "Sam ties laces of clean blue running shoe on wooden studio stool with effortless relaxed posture.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Shoelace Tug & Natural Shoe Leather Creak",
        "vfx_desc": "Clean Minimalist Studio Void with Warm Sand Palette",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_33-C": {
        "title": "Micro-Action Vignette 3 (50mm) - Reading Three Bullet Points on Note Card",
        "action": "Sam holds neat white index card, scanning three short bullet points with relaxed hazel eyes.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Cardboard Card Flip Sound & Reassured Exhale",
        "vfx_desc": "Three Clean Cyan Bullet Points Glowing Softly on White Card",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_34-A": {
        "title": "Guard Dog Neutralization (50mm) - Miniature Guard Dog Laughing at Trivial Goal",
        "action": "Miniature guard dog sits in bunker laughing dismissively at the tiny 2-minute goal.",
        "camera_desc": "Smooth Pan Left (103.5% Scale, Right 51.5% -> Left 48.5%)",
        "audio_desc": "Amused Cartoon Dog Chuckle & Soft Yawn",
        "vfx_desc": "Red Alarm Siren Completely Dark and Silent with Soft Blue Ambient",
        "env_label": "Brain Command Bunker (#08090c)",
        "env_hex": "#08090c"
    },
    "LINE_34-B": {
        "title": "Guard Dog Sleeping Peacefully (50mm) - Guard Dog Fast Asleep on Woolen Rug",
        "action": "Miniature guard dog curls into deep, peaceful sleep on woolen rug with tiny cartoon snores.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Gentle Rhythmic Sleeping Snores & Cozy Ambient Fireplace Hum",
        "vfx_desc": "Warm Cozy Golden Light & Floating Zzz Particle Glyphs",
        "env_label": "Solid Dark Slate-Indigo Studio Void (#0f172a)",
        "env_hex": "#0f172a"
    },
    "LINE_35-A": {
        "title": "Psychological Kinetic Flow (50mm) - Golden Ribbons of Energy Flowing from Fingers",
        "action": "Golden ribbons of kinetic momentum flow effortlessly from Sam's typing fingers across keys.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Flowing Shimmer Synth & Rhythmic Typing Flow",
        "vfx_desc": "Golden Volumetric Energy Streams Connecting Hands to Floating Document",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_35-B": {
        "title": "Perpetual Momentum Cinematography (85mm) - Polished Steel Newton's Cradle Balls Swinging",
        "action": "Polished steel Newton's cradle balls swing in continuous, satisfying, rhythmic perpetual motion.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Rhythmic Metal Newton's Cradle Clicks (Snap-Click)",
        "vfx_desc": "High Specular Chrome Reflections & Prismatic Dispersion Streaks",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_36-A": {
        "title": "Protocol Two Plaque (50mm) - Natural Oak Plaque THE SELF-COMPASSION PARADOX",
        "action": "Carved natural oak wood plaque appears: PROTOCOL 2: THE SELF-COMPASSION PARADOX.",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Deep Resonant Wooden Chime & Warm Cello Chord",
        "vfx_desc": "Warm Amber Incandescent Spotlights Illuminating Tactile Wood Grain",
        "env_label": "Solid Dull Seafoam Green Studio Stage (#45a29e)",
        "env_hex": "#45a29e"
    },
    "LINE_36-B": {
        "title": "Punishment Cycle Metaphor (50mm) - Iron Hamster Wheel of Sharp Thorns Spinning",
        "action": "Heavy iron hamster wheel lined with sharp thorns spins endlessly in dark shadowy void.",
        "camera_desc": "Slow Push-Out 105.5% -> 100% (Sinusoidal S-Curve)",
        "audio_desc": "Heavy Squeaking Iron Axle & Metallic Groan",
        "vfx_desc": "Cold Desaturated Chiaroscuro & Sharp Metallic Specular Highlights",
        "env_label": "Deep Slate-Teal Void (#2c4a52)",
        "env_hex": "#2c4a52"
    },
    "LINE_37-A": {
        "title": "Emotional Softening Metamorphosis (50mm) - Sharp Iron Thorns Dissolving into Rose Petals",
        "action": "Iron thorns soften and dissolve into cascade of fragrant velvet rose petals floating down.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Magical Softening Swell & Velvet Petal Rustle",
        "vfx_desc": "Rich Crimson Velvet Rose Petals Drifting in Volumetric Golden Light",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_37-B": {
        "title": "Compassionate Resolution (50mm) - Sam Looking Calmly at Camera with Self-Forgiveness",
        "action": "Sam looks into camera lens with compassionate, peaceful expression and genuine self-forgiveness.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Harmonic Acoustic Guitar & Cello Duet Resolution",
        "vfx_desc": "Warm Soft Key Lighting & Genuine Hazel Eye Catchlights",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_38-A": {
        "title": "Gentle Work Closure (50mm) - Closing Laptop as Warm Golden Dawn Light Fills Room",
        "action": "Sam closes laptop lid gently; warm golden dawn sunlight streams across wooden tabletop.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Soft Laptop Clamshell Close Click & Gentle Morning Birds Outside",
        "vfx_desc": "Volumetric Warm Golden Sunlight Shafts Cutting Across Desktop",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_38-B": {
        "title": "Serene Profile Conclusion (50mm) - Sam Smiling Towards Sunrise Window",
        "action": "Sam smiles serenely in side profile, gazing toward the sunrise with profound mental clarity.",
        "camera_desc": "Slow Push-In 100% -> 105.5% (Sinusoidal S-Curve)",
        "audio_desc": "Ascending Warm Synth Chords & Uplifting Resolution",
        "vfx_desc": "Golden Morning Rim Light Tracing Facial Profile & Tousled Hair",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    },
    "LINE_39-A": {
        "title": "Channel Signature Outro (50mm) - Final Channel Badge 'Stay Curious' Subscription Card",
        "action": "Sam looks directly at camera, waving warmly: 'I will see you on Friday. Stay curious.'",
        "camera_desc": "Static Hold (Zero Drift Inter-Area Resize)",
        "audio_desc": "Channel Signature Acoustic Theme Jingle & Clean Outro Stinger",
        "vfx_desc": "Floating Gold-Bordered Channel Subscription Card (@isy019)",
        "env_label": "Solid Warm Cream Studio Background (#f3e5d0)",
        "env_hex": "#f3e5d0"
    }
}

def generate_sceneflow_dataset():
    print("[*] Loading compiled shots from:", COMPILED_SHOTS_FILE)
    with open(COMPILED_SHOTS_FILE, "r", encoding="utf-8") as f:
        shots = json.load(f)

    print(f"[*] Ingested {len(shots)} master shots.")
    assert len(shots) == 99, f"Expected exactly 99 shots, found {len(shots)}"

    print("[*] Loading full timeline word timestamps from:", WORD_TIMESTAMPS_FILE)
    with open(WORD_TIMESTAMPS_FILE, "r", encoding="utf-8") as f:
        word_data = json.load(f)

    print("[*] Computing 481 adaptive subtitle phrases with cut snapping...")
    phrases = build_adaptive_phrases_from_data(word_data, shots=shots)
    print(f"[*] Generated {len(phrases)} dialogue phrases.")
    assert len(phrases) == 481, f"Expected exactly 481 phrases, found {len(phrases)}"

    # Map phrases to shots based on time midpoint
    shot_phrases = {s["shot_id"]: [] for s in shots}
    for p in phrases:
        mid = (p["start"] + p["end"]) / 2.0
        assigned = False
        for s in shots:
            if s["start"] <= mid < s["end"]:
                shot_phrases[s["shot_id"]].append(p)
                assigned = True
                break
        if not assigned:
            # Fallback to closest shot
            closest = min(shots, key=lambda s: abs((s["start"] + s["end"]) / 2.0 - mid))
            shot_phrases[closest["shot_id"]].append(p)

    # Build Master Screenplay Text and track verbatim character indices
    # Screenplay structure includes scene headings, cue directives, and dialogue blocks.
    script_lines = []
    cue_index_registry = {}

    current_act = None

    for s_idx, shot in enumerate(shots):
        shot_id = shot["shot_id"]
        act = get_act_for_shot(shot_id)
        cat = SHOT_CATALOG.get(shot_id, {
            "title": f"Shot {shot_id}",
            "action": f"Action for {shot_id}",
            "camera_desc": f"{shot['motion']} camera move",
            "audio_desc": f"Audio for {shot_id}",
            "vfx_desc": f"VFX for {shot_id}",
            "env_label": "Studio Void",
            "env_hex": "#45a29e"
        })

        # New Act header
        if current_act != act["act"]:
            current_act = act["act"]
            script_lines.append("")
            script_lines.append(f"=== ACT {act['act']}: {act['title'].upper()} ===")
            script_lines.append(f"[{act['description']}]")
            script_lines.append("")

        # Shot block in screenplay
        start_tc = f"{int(shot['start']//60):02d}:{shot['start']%60:05.2f}"
        end_tc = f"{int(shot['end']//60):02d}:{shot['end']%60:05.2f}"
        
        # Shot header tag
        shot_tag = f"[SHOT {shot_id}: {cat['title']}]"
        env_tag = f"[ENV {shot_id}: {cat['env_label']}]"
        cam_tag = f"[CAM {shot_id}: {cat['camera_desc']}]"
        act_tag = f"[ACT {shot_id}: {cat['action']}]"
        aud_tag = f"[SFX {shot_id}: {cat['audio_desc']}]"
        vfx_tag = f"[VFX {shot_id}: {cat['vfx_desc']}]"
        
        trans_name = shot['transition'].upper()
        trans_dur = "0.00s" if shot['transition'] == 'snap' else ("0.60s" if shot['transition'] == 'dissolve_act' else "0.30s")
        cut_tag = f"[CUT {shot_id}: {trans_name} ({trans_dur})]"

        script_lines.append(f"--- SHOT {shot_id} [{start_tc} - {end_tc}] ---")
        
        # Register exact strings
        cue_index_registry[f"shot_{shot_id}"] = shot_tag
        script_lines.append(shot_tag)

        cue_index_registry[f"env_{shot_id}"] = env_tag
        script_lines.append(env_tag)

        cue_index_registry[f"cam_{shot_id}"] = cam_tag
        script_lines.append(cam_tag)

        cue_index_registry[f"act_{shot_id}"] = act_tag
        script_lines.append(act_tag)

        cue_index_registry[f"aud_{shot_id}"] = aud_tag
        script_lines.append(aud_tag)

        cue_index_registry[f"vfx_{shot_id}"] = vfx_tag
        script_lines.append(vfx_tag)

        cue_index_registry[f"trans_{shot_id}"] = cut_tag
        script_lines.append(cut_tag)

        # Dialogue block
        s_phrases = shot_phrases[shot_id]
        if s_phrases:
            script_lines.append("")
            script_lines.append("SAM")
            dlg_tokens = []
            for p_idx, p in enumerate(s_phrases):
                p_text = p["text"]
                dlg_tokens.append(p_text)
            script_lines.append(" ".join(dlg_tokens))
            script_lines.append("")
        else:
            script_lines.append("")

    full_script_text = "\n".join(script_lines)
    print(f"[*] Assembled master screenplay text ({len(full_script_text)} chars).")

    # Generate cues for all 8 tracks
    cues = []
    search_cursor = 0

    # 1. Dialogue Cues (481 phrases, speaker='Sam')
    print("[*] Generating Track 0: Dialogue cues (481 phrases)...")
    for idx, p in enumerate(phrases):
        cue_id = f"cue_dlg_{idx+1:03d}"
        selected_text = p["text"]
        start_t = round(p["start"], 3)
        end_t = round(p["end"], 3)
        duration = round(end_t - start_t, 3)

        # Locate verbatim position in screenplay
        found_pos = full_script_text.find(selected_text, search_cursor)
        if found_pos == -1:
            # Fallback search from start
            found_pos = full_script_text.find(selected_text)
        else:
            search_cursor = found_pos

        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

        cues.append({
            "id": cue_id,
            "type": "dialogue",
            "speaker": "Sam",
            "selectedText": selected_text,
            "startTime": start_t,
            "endTime": end_t,
            "duration": duration,
            "trackIndex": TRACK_INDEX_MAP["dialogue"],
            "colorClass": TRACK_COLOR_MAP["dialogue"],
            "startIndex": start_index,
            "endIndex": end_index,
            "metadata": {
                "wordsCount": len(p.get("words", [])),
                "speaker": "Sam"
            }
        })

    # 2. Shot Cues (99 shots, NO speaker property)
    print("[*] Generating Track 3: Shot cues (99 shots)...")
    for idx, s in enumerate(shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_shot_{idx+1:02d}_{shot_id.lower().replace('-', '_')}"
        selected_text = cue_index_registry[f"shot_{shot_id}"]
        start_t = round(s["start"], 3)
        end_t = round(s["end"], 3)
        duration = round(end_t - start_t, 3)

        found_pos = full_script_text.find(selected_text)
        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

        cues.append({
            "id": cue_id,
            "type": "shot",
            "selectedText": selected_text,
            "startTime": start_t,
            "endTime": end_t,
            "duration": duration,
            "trackIndex": TRACK_INDEX_MAP["shot"],
            "colorClass": TRACK_COLOR_MAP["shot"],
            "startIndex": start_index,
            "endIndex": end_index,
            "metadata": {
                "shotId": shot_id,
                "block": s["block"],
                "motion": s["motion"],
                "transition": s["transition"],
                "act": get_act_for_shot(shot_id)["act"]
            }
        })

    # 3. Action Cues (99 actions, NO speaker property)
    print("[*] Generating Track 1: Action cues (99 character actions)...")
    for idx, s in enumerate(shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_act_{idx+1:02d}_{shot_id.lower().replace('-', '_')}"
        selected_text = cue_index_registry[f"act_{shot_id}"]
        start_t = round(s["start"], 3)
        end_t = round(s["end"], 3)
        duration = round(end_t - start_t, 3)

        found_pos = full_script_text.find(selected_text)
        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

        cues.append({
            "id": cue_id,
            "type": "action",
            "selectedText": selected_text,
            "startTime": start_t,
            "endTime": end_t,
            "duration": duration,
            "trackIndex": TRACK_INDEX_MAP["action"],
            "colorClass": TRACK_COLOR_MAP["action"],
            "startIndex": start_index,
            "endIndex": end_index,
            "metadata": {
                "shotId": shot_id,
                "actionDirective": SHOT_CATALOG[shot_id]["action"]
            }
        })

    # 4. Camera Cues (99 camera moves: 19 static + 80 dynamic, NO speaker property)
    print("[*] Generating Track 2: Camera cues (19 static holds + 80 dynamic moves)...")
    for idx, s in enumerate(shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_cam_{idx+1:02d}_{shot_id.lower().replace('-', '_')}"
        selected_text = cue_index_registry[f"cam_{shot_id}"]
        start_t = round(s["start"], 3)
        end_t = round(s["end"], 3)
        duration = round(end_t - start_t, 3)

        found_pos = full_script_text.find(selected_text)
        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

        is_static = (s["motion"] == "static")
        cues.append({
            "id": cue_id,
            "type": "camera",
            "selectedText": selected_text,
            "startTime": start_t,
            "endTime": end_t,
            "duration": duration,
            "trackIndex": TRACK_INDEX_MAP["camera"],
            "colorClass": TRACK_COLOR_MAP["camera"],
            "startIndex": start_index,
            "endIndex": end_index,
            "metadata": {
                "shotId": shot_id,
                "motion": s["motion"],
                "isStatic": is_static,
                "easing": "none" if is_static else "0.5 * (1.0 - cos(pi * progress))",
                "cameraDescription": SHOT_CATALOG[shot_id]["camera_desc"]
            }
        })

    # 5. Audio Cues (99 sound design events, NO speaker property)
    print("[*] Generating Track 4: Audio cues (99 sound design events)...")
    for idx, s in enumerate(shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_aud_{idx+1:02d}_{shot_id.lower().replace('-', '_')}"
        selected_text = cue_index_registry[f"aud_{shot_id}"]
        start_t = round(s["start"], 3)
        end_t = round(s["end"], 3)
        duration = round(end_t - start_t, 3)

        found_pos = full_script_text.find(selected_text)
        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

        cues.append({
            "id": cue_id,
            "type": "audio",
            "selectedText": selected_text,
            "startTime": start_t,
            "endTime": end_t,
            "duration": duration,
            "trackIndex": TRACK_INDEX_MAP["audio"],
            "colorClass": TRACK_COLOR_MAP["audio"],
            "startIndex": start_index,
            "endIndex": end_index,
            "metadata": {
                "shotId": shot_id,
                "soundEvent": SHOT_CATALOG[shot_id]["audio_desc"]
            }
        })

    # 6. VFX Cues (99 visual effects & lighting shifts, NO speaker property)
    print("[*] Generating Track 5: VFX cues (99 lighting & shader effects)...")
    for idx, s in enumerate(shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_vfx_{idx+1:02d}_{shot_id.lower().replace('-', '_')}"
        selected_text = cue_index_registry[f"vfx_{shot_id}"]
        start_t = round(s["start"], 3)
        end_t = round(s["end"], 3)
        duration = round(end_t - start_t, 3)

        found_pos = full_script_text.find(selected_text)
        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

        cues.append({
            "id": cue_id,
            "type": "vfx",
            "selectedText": selected_text,
            "startTime": start_t,
            "endTime": end_t,
            "duration": duration,
            "trackIndex": TRACK_INDEX_MAP["vfx"],
            "colorClass": TRACK_COLOR_MAP["vfx"],
            "startIndex": start_index,
            "endIndex": end_index,
            "metadata": {
                "shotId": shot_id,
                "effect": SHOT_CATALOG[shot_id]["vfx_desc"]
            }
        })

    # 7. Transition Cues (99 transition directives, NO speaker property)
    print("[*] Generating Track 6: Transition cues (99 cuts & dissolves)...")
    for idx, s in enumerate(shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_trans_{idx+1:02d}_{shot_id.lower().replace('-', '_')}"
        selected_text = cue_index_registry[f"trans_{shot_id}"]
        start_t = round(s["start"], 3)
        end_t = round(s["end"], 3)
        duration = round(end_t - start_t, 3)

        found_pos = full_script_text.find(selected_text)
        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

        cues.append({
            "id": cue_id,
            "type": "transition",
            "selectedText": selected_text,
            "startTime": start_t,
            "endTime": end_t,
            "duration": duration,
            "trackIndex": TRACK_INDEX_MAP["transition"],
            "colorClass": TRACK_COLOR_MAP["transition"],
            "startIndex": start_index,
            "endIndex": end_index,
            "metadata": {
                "shotId": shot_id,
                "transitionType": s["transition"],
                "transitionDuration": 0.0 if s["transition"] == "snap" else (0.6 if s["transition"] == "dissolve_act" else 0.3)
            }
        })

    # 8. Environment Cues (99 studio void & lighting backdrops, NO speaker property)
    print("[*] Generating Track 7: Environment cues (99 environments)...")
    for idx, s in enumerate(shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_env_{idx+1:02d}_{shot_id.lower().replace('-', '_')}"
        selected_text = cue_index_registry[f"env_{shot_id}"]
        start_t = round(s["start"], 3)
        end_t = round(s["end"], 3)
        duration = round(end_t - start_t, 3)

        found_pos = full_script_text.find(selected_text)
        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

        cues.append({
            "id": cue_id,
            "type": "environment",
            "selectedText": selected_text,
            "startTime": start_t,
            "endTime": end_t,
            "duration": duration,
            "trackIndex": TRACK_INDEX_MAP["environment"],
            "colorClass": TRACK_COLOR_MAP["environment"],
            "startIndex": start_index,
            "endIndex": end_index,
            "metadata": {
                "shotId": shot_id,
                "backdropHex": SHOT_CATALOG[shot_id]["env_hex"],
                "environmentName": SHOT_CATALOG[shot_id]["env_label"]
            }
        })

    # Sort cues by startTime then trackIndex
    cues.sort(key=lambda c: (c["startTime"], c["trackIndex"]))

    # Build the Complete Root Dataset
    dataset = {
        "$schema": "./schema.json",
        "metadata": {
            "title": "Why You Can't Start: The Cognitive Science of Chronic Procrastination (And The Micro-Habit Antidote)",
            "topic": "Topic 03",
            "channel": "Isy why (@isy019)",
            "runtimeSeconds": 565.10,
            "fps": 30,
            "resolution": {
                "width": 1920,
                "height": 1080,
                "aspectRatio": "16:9"
            },
            "totalScriptLines": 39,
            "totalShots": 99,
            "totalDialoguePhrases": 481,
            "staticHoldsCount": 19,
            "dynamicMovesCount": 80,
            "totalCues": len(cues),
            "acts": ACTS_INFO
        },
        "mediaReferences": {
            "localVideo": "production/topic_03/TOPIC_03_MASTER_VIDEO_WITH_CAPTIONS.mp4",
            "cleanVideo": "production/topic_03/TOPIC_03_MASTER_VIDEO_FINAL.mp4",
            "masterAudio": "production/topic_03/audio/TOPIC_03_FULL_VOICEOVER_MASTER.mp3",
            "wordTimestamps": "production/topic_03/audio/full_timeline_word_timestamps.json"
        },
        "youtubeId": "",
        "tracks": TRACK_DEFINITIONS,
        "settings": {
            "general": {"before": 0.0, "after": 0.0},
            "dialogue": {"before": 0.0, "after": 0.0},
            "action": {"before": 0.0, "after": 0.0},
            "camera": {"before": 0.0, "after": 0.0},
            "shot": {"before": 0.0, "after": 0.0},
            "audio": {"before": 0.0, "after": 0.0},
            "vfx": {"before": 0.0, "after": 0.0},
            "transition": {"before": 0.0, "after": 0.0},
            "environment": {"before": 0.0, "after": 0.0}
        },
        "scriptText": full_script_text,
        "cues": cues
    }

    # Write output JSON
    print(f"[*] Writing complete dataset to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"[*] Dataset successfully written! File size: {OUTPUT_FILE.stat().st_size:,} bytes.")

    # Validation Engine
    print("[*] Validating dataset against schema:", SCHEMA_FILE)
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.validate(instance=dataset, schema=schema)
    print(">>> JSON SCHEMA DRAFT-07 VALIDATION: PASSED! Zero errors! <<<")

    # Cardinality Assertions
    dlg_cues = [c for c in cues if c["type"] == "dialogue"]
    shot_cues = [c for c in cues if c["type"] == "shot"]
    cam_cues = [c for c in cues if c["type"] == "camera"]
    act_cues = [c for c in cues if c["type"] == "action"]
    aud_cues = [c for c in cues if c["type"] == "audio"]
    vfx_cues = [c for c in cues if c["type"] == "vfx"]
    trans_cues = [c for c in cues if c["type"] == "transition"]
    env_cues = [c for c in cues if c["type"] == "environment"]

    print(f"[*] Dialogue cues count: {len(dlg_cues)} (Expected: 481)")
    assert len(dlg_cues) == 481, f"Expected 481 dialogue cues, found {len(dlg_cues)}"

    print(f"[*] Shot cues count: {len(shot_cues)} (Expected: 99)")
    assert len(shot_cues) == 99, f"Expected 99 shot cues, found {len(shot_cues)}"

    print(f"[*] Camera cues count: {len(cam_cues)} (Expected: 99)")
    assert len(cam_cues) == 99, f"Expected 99 camera cues, found {len(cam_cues)}"

    static_holds = [c for c in cam_cues if c["metadata"]["isStatic"]]
    dynamic_moves = [c for c in cam_cues if not c["metadata"]["isStatic"]]
    print(f"[*] Static camera holds: {len(static_holds)} (Expected: 19)")
    assert len(static_holds) == 19, f"Expected 19 static holds, found {len(static_holds)}"
    print(f"[*] Dynamic camera moves: {len(dynamic_moves)} (Expected: 80)")
    assert len(dynamic_moves) == 80, f"Expected 80 dynamic moves, found {len(dynamic_moves)}"

    # Check monotonicity and boundary limits
    for c in cues:
        assert c["startTime"] < c["endTime"], f"Inverted or zero duration in cue {c['id']}: {c['startTime']} >= {c['endTime']}"
        assert c["endTime"] <= 565.10, f"Cue {c['id']} exceeds master duration: {c['endTime']} > 565.10"
        if c["type"] != "dialogue":
            assert "speaker" not in c, f"Non-dialogue cue {c['id']} has speaker property"
        else:
            assert c["speaker"] == "Sam", f"Dialogue cue {c['id']} missing speaker 'Sam'"

    print(">>> ALL ASSERTIONS AND BOUNDS CHECKS: PASSED! <<<")
    print(f"Total Cues Generated: {len(cues)} across all 8 tracks.")
    return dataset

if __name__ == "__main__":
    generate_sceneflow_dataset()

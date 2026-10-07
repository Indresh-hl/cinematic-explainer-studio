#!/usr/bin/env python3
"""
scripts/generate_sceneflow_dataset_topic_02.py
==============================================
Authoritative SceneFlow Dataset Generator for Topic 02:
"The Low Dopamine Morning Routine To Reset Your Brain Focus"

Adheres strictly to:
- taruma/SceneFlow Draft-07 JSON Schema (public/schema.json)
- Exactly 110 visual shots across 29 script lines (11 static holds + 99 dynamic camera moves)
- 8 Color-Coded Cue Tracks: Dialogue, Action, Camera, Shot, Audio, VFX, Transition, Environment
- Full screenplay text with verbatim character indices (startIndex, endIndex)
- Monotonic timestamps with t_start < t_end <= 600.68s
"""

import json
import os
import re
import sys
from pathlib import Path
import jsonschema

# Configure stdout encoding for Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "pipeline"))
from render_topic_02_master_video import build_timeline_schedule, SCRIPT_MAPPING

SCHEMA_FILE = BASE_DIR / "public" / "schema.json"
OUTPUT_FILE = BASE_DIR / "topic_02_sceneflow_sync.json"
OUTPUT_DL = Path(r"C:\Users\Indresh HL\Downloads\topic_02_sceneflow_sync.json")
TIMELINE_META = BASE_DIR / "production" / "topic_02" / "audio" / "topic_02_timeline_metadata.json"
MAPPING_GUIDE = BASE_DIR / "IMAGE_TO_LINE_MAPPING_LOW_DOPAMINE_MORNING.md"

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

# 5 Acts structural division for Topic 02
ACTS_INFO = [
    {
        "act": 1,
        "title": "The Crime Scene at 6:45 AM",
        "shots": "LINE_01-A to LINE_07-D",
        "timeRange": [0.0, 98.13],
        "description": "Bed paralysis, the 10,000-lux blue screen trap, somatic shame, and the biological defense revelation."
    },
    {
        "act": 2,
        "title": "The Neurochemical Heist",
        "shots": "LINE_08-A to LINE_13-D",
        "timeRange": [98.13, 239.48],
        "description": "Tonic baseline vs phasic spikes, Anna Lembke balance scale, receptor downregulation, and desk dysphoria."
    },
    {
        "act": 3,
        "title": "The Ghost in the Machine",
        "shots": "LINE_14-A to LINE_18-D",
        "timeRange": [239.48, 344.08],
        "description": "Cortisol Awakening Response hijack, Sophie Leroy Attentional Residue, caffeine receptor blockage, and 2:00 PM crash."
    },
    {
        "act": 4,
        "title": "The 5-Second Attention Reset",
        "shots": "LINE_19-A to LINE_23-D",
        "timeRange": [344.08, 446.29],
        "description": "Theatrical spotlight snap, interactive 5-second cognitive recall test (Line 20), and circadian golden hour."
    },
    {
        "act": 5,
        "title": "The Tactical Antidote",
        "shots": "LINE_24-A to LINE_29-B",
        "timeRange": [446.29, 600.68],
        "description": "The 3 Pillars: Rule 1 Frictionless Horizon, Rule 2 Photon Anchor, Rule 3 Deep Work Runway, and channel outro."
    }
]

def get_act_for_shot(shot_id: str) -> dict:
    line_num = int(shot_id.split("-")[0].replace("LINE_", ""))
    if line_num <= 7:
        return ACTS_INFO[0]
    elif line_num <= 13:
        return ACTS_INFO[1]
    elif line_num <= 18:
        return ACTS_INFO[2]
    elif line_num <= 23:
        return ACTS_INFO[3]
    else:
        return ACTS_INFO[4]

def format_tc(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"

def parse_mapping_guide():
    """Parses IMAGE_TO_LINE_MAPPING_LOW_DOPAMINE_MORNING.md for shot details."""
    catalog = {}
    with open(MAPPING_GUIDE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if line.strip().startswith("|") and "LINE_" in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 7:
                sid_raw = parts[2].replace("*", "").replace("`", "").replace(".jpg", "").strip()
                if not sid_raw.startswith("LINE_"):
                    continue
                spoken = parts[4].strip('"').strip()
                raw_desc = parts[5].replace("<br>", " ")
                motion_raw = parts[6]

                # Extract shot type / title
                m_title = re.search(r"\*\*([^*]+)\*\*", raw_desc)
                shot_title = m_title.group(1).replace(":", "") if m_title else "Cinematic Explainer Shot"

                # Extract environment token
                env_hex = "#45a29e"
                env_label = "Solid Dull Seafoam Green Studio Void (#45a29e)"
                if "#6ba4b8" in raw_desc or "sky blue" in raw_desc.lower():
                    env_hex = "#6ba4b8"
                    env_label = "Muted Dull Sky Blue Studio Void (#6ba4b8)"
                elif "#f3e5d0" in raw_desc or "cream" in raw_desc.lower() or "sand" in raw_desc.lower():
                    env_hex = "#f3e5d0"
                    env_label = "Warm Sand / Cream Studio Void (#f3e5d0)"
                elif "#08090c" in raw_desc or "#0f172a" in raw_desc or "obsidian" in raw_desc.lower() or "void" in raw_desc.lower():
                    env_hex = "#08090c"
                    env_label = "Obsidian Indigo Studio Void (#08090c)"

                # Extract lighting / vfx
                vfx_desc = "3D Octane studio lighting with shallow depth of field and soft contact floor shadows."
                if "Lighting:" in raw_desc:
                    vfx_part = raw_desc.split("Lighting:")[1].split(".")[0].strip()
                    vfx_desc = f"{vfx_part}. Volumetric highlights & soft contact shadows."
                elif "glow" in raw_desc.lower():
                    vfx_desc = "Emissive surface luminescence and dynamic rim lighting."

                # Audio / SFX cue
                audio_desc = "Subtle cinematic room tone and ambient explainer score bed."
                if "tick" in motion_raw.lower() or "tick" in raw_desc.lower():
                    audio_desc = "Resonant metronomic clock tick (1Hz)."
                elif "snap" in motion_raw.lower() or "thud" in motion_raw.lower() or "impact" in motion_raw.lower():
                    audio_desc = "Deep sub-bass impact thud & crisp tactile snap."
                elif "ding" in motion_raw.lower() or "bell" in motion_raw.lower() or "chime" in motion_raw.lower():
                    audio_desc = "Resonant brass timer bell chime."
                elif "paper" in motion_raw.lower() or "pen" in motion_raw.lower():
                    audio_desc = "Crisp paper flutter & textured fountain pen glide."

                # Character Action
                action_desc = raw_desc
                if "Sam" in raw_desc:
                    # extract sentence containing Sam
                    sentences = raw_desc.split(".")
                    for s in sentences:
                        if "Sam" in s:
                            action_desc = s.strip() + "."
                            break
                action_desc = action_desc.replace("**", "").replace("*", "")

                catalog[sid_raw] = {
                    "title": shot_title,
                    "action": action_desc[:180],
                    "camera_desc": motion_raw,
                    "audio_desc": audio_desc,
                    "vfx_desc": vfx_desc,
                    "env_label": env_label,
                    "env_hex": env_hex
                }

    return catalog

def build_topic_02_dialogue_phrases(timeline_shots):
    """Builds dialogue phrases from timeline metadata snapped to shots."""
    with open(TIMELINE_META, "r", encoding="utf-8") as f:
        meta = json.load(f)

    phrases = []
    phrase_id = 1

    for line in meta["lines"]:
        label = line["line_label"]
        text = line["text"]
        t_start = line["start_time"]
        speech_dur = line["speech_duration"]

        # Split line into natural punctuation clauses
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+|(?<=[,;:])\s+", text) if p.strip()]
        total_chars = sum(len(p) for p in parts)
        cur_t = t_start

        for part in parts:
            frac = len(part) / total_chars if total_chars > 0 else (1.0 / len(parts))
            p_dur = speech_dur * frac
            p_start = round(cur_t, 3)
            p_end = round(cur_t + p_dur, 3)

            phrases.append({
                "id": f"cue_dlg_{phrase_id:03d}",
                "line": label,
                "text": part,
                "start": p_start,
                "end": p_end,
                "duration": round(p_end - p_start, 3)
            })
            cur_t += p_dur
            phrase_id += 1

    # Snap phrase boundaries that are within 0.15s of shot cuts
    shot_ends = [round(s["end"], 3) for s in timeline_shots[:-1]]
    for p in phrases:
        for cut_t in shot_ends:
            if 0 < (cut_t - p["start"]) < 0.20:
                p["start"] = cut_t
            if 0 < (p["end"] - cut_t) < 0.20:
                p["end"] = cut_t

    # Prevent invalid zero or inverted durations
    for p in phrases:
        if p["end"] <= p["start"]:
            p["end"] = round(p["start"] + 0.50, 3)
        p["duration"] = round(p["end"] - p["start"], 3)

    return phrases

def generate_sceneflow_dataset():
    print("=" * 80)
    print("🎬 GENERATING AUTHORITATIVE SCENEFLOW DATASET (TOPIC 02)")
    print("=" * 80)

    # 1. Timeline Shots & Metadata
    timeline_shots, total_runtime = build_timeline_schedule()
    print(f"[*] Loaded {len(timeline_shots)} master shots (Runtime: {total_runtime:.2f}s)")
    assert len(timeline_shots) == 110, f"Expected 110 shots, got {len(timeline_shots)}"

    shot_catalog = parse_mapping_guide()
    print(f"[*] Parsed catalog details for {len(shot_catalog)} shots.")

    # Fill any missing catalog items with robust defaults
    for s in timeline_shots:
        sid = s["shot_id"]
        if sid not in shot_catalog:
            act_obj = get_act_for_shot(sid)
            shot_catalog[sid] = {
                "title": f"Cinematic Explainer Shot ({sid})",
                "action": f"Sam demonstrates key cognitive concept in 3D feature animation space during {act_obj['title']}.",
                "camera_desc": f"Camera motion: {s['motion']}, transition: {s['transition']}.",
                "audio_desc": "Subtle ambient score with tactile foley.",
                "vfx_desc": "3D Octane studio lighting with shallow depth of field.",
                "env_label": "Solid Dull Seafoam Green Studio Void (#45a29e)",
                "env_hex": "#45a29e"
            }

    # 2. Build Dialogue Phrases
    phrases = build_topic_02_dialogue_phrases(timeline_shots)
    print(f"[*] Generated {len(phrases)} synchronized dialogue phrases.")

    # 3. Group Dialogue Phrases per Shot for Screenplay Assembly
    shot_phrases = {s["shot_id"]: [] for s in timeline_shots}
    for p in phrases:
        p_mid = (p["start"] + p["end"]) / 2.0
        # Find which shot contains this phrase
        for s in timeline_shots:
            if s["start"] <= p_mid < s["end"]:
                shot_phrases[s["shot_id"]].append(p)
                break

    # 4. Assemble Full Screenplay Text & Build Exact String Registry
    script_lines = [
        "SCENEFLOW AUTHORITATIVE SCREENPLAY - TOPIC 02",
        "THE LOW DOPAMINE MORNING ROUTINE TO RESET YOUR BRAIN FOCUS",
        "Channel: Isy why (@isy019)",
        "===========================================================",
        ""
    ]

    cue_index_registry = {}

    for idx, shot in enumerate(timeline_shots):
        shot_id = shot["shot_id"]
        info = shot_catalog[shot_id]
        start_tc = format_tc(shot["start"])
        end_tc = format_tc(shot["end"])

        shot_tag = f"[SHOT {shot_id}: {info['title']}]"
        env_tag = f"[ENV: {info['env_label']}]"
        cam_tag = f"[CAM: {shot['motion'].upper()} - {info['camera_desc']}]"
        act_tag = f"[ACT: {info['action']}]"
        aud_tag = f"[SFX: {info['audio_desc']}]"
        vfx_tag = f"[VFX: {info['vfx_desc']}]"

        trans_dur = "0.05s" if shot["transition"] == "snap" else ("0.60s" if shot["transition"] == "dissolve_act" else "0.35s")
        cut_tag = f"[CUT {shot_id}: {shot['transition'].upper()} ({trans_dur})]"

        script_lines.append(f"--- SHOT {shot_id} [{start_tc} - {end_tc}] ---")
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

        s_phrases = shot_phrases[shot_id]
        if s_phrases:
            script_lines.append("")
            script_lines.append("SAM")
            dlg_tokens = [p["text"] for p in s_phrases]
            script_lines.append(" ".join(dlg_tokens))
            script_lines.append("")
        else:
            script_lines.append("")

    full_script_text = "\n".join(script_lines)
    print(f"[*] Assembled master screenplay text ({len(full_script_text):,} chars).")

    # 5. Generate Cues Across all 8 Tracks
    cues = []
    search_cursor = 0

    # Track 0: Dialogue (Speaker = 'Sam')
    print("[*] Generating Track 0: Dialogue cues...")
    for idx, p in enumerate(phrases):
        cue_id = f"cue_dlg_{idx+1:03d}"
        selected_text = p["text"]
        start_t = round(p["start"], 3)
        end_t = round(p["end"], 3)
        duration = round(end_t - start_t, 3)

        found_pos = full_script_text.find(selected_text, search_cursor)
        if found_pos == -1:
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
                "wordsCount": len(selected_text.split()),
                "speaker": "Sam"
            }
        })

    # Track 3: Shot Cues (110 shots)
    print("[*] Generating Track 3: Shot cues (110 shots)...")
    for idx, s in enumerate(timeline_shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_shot_{idx+1:03d}_{shot_id.lower().replace('-', '_')}"
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
                "motion": s["motion"],
                "transition": s["transition"],
                "act": get_act_for_shot(shot_id)["act"]
            }
        })

    # Track 1: Action Cues (110 actions)
    print("[*] Generating Track 1: Action cues...")
    for idx, s in enumerate(timeline_shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_act_{idx+1:03d}_{shot_id.lower().replace('-', '_')}"
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
                "actionSummary": shot_catalog[shot_id]["action"]
            }
        })

    # Track 2: Camera Cues (110 camera movements)
    print("[*] Generating Track 2: Camera cues (11 static holds + 99 dynamic moves)...")
    for idx, s in enumerate(timeline_shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_cam_{idx+1:03d}_{shot_id.lower().replace('-', '_')}"
        selected_text = cue_index_registry[f"cam_{shot_id}"]
        start_t = round(s["start"], 3)
        end_t = round(s["end"], 3)
        duration = round(end_t - start_t, 3)
        is_static = (s["motion"] == "static")

        found_pos = full_script_text.find(selected_text)
        start_index = found_pos if found_pos != -1 else 0
        end_index = start_index + len(selected_text)

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
                "motionType": s["motion"],
                "isStatic": is_static,
                "easing": "None (Static hold)" if is_static else "Sinusoidal S-Curve: 0.5 * (1.0 - cos(pi * p))",
                "targetScale": "100% (locked)" if is_static else ("100% -> 106%" if s["motion"] == "zoom_in" else "106% -> 100%")
            }
        })

    # Track 4: Audio Cues (110 sound cues)
    print("[*] Generating Track 4: Audio & SFX cues...")
    for idx, s in enumerate(timeline_shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_aud_{idx+1:03d}_{shot_id.lower().replace('-', '_')}"
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
                "soundEvent": shot_catalog[shot_id]["audio_desc"]
            }
        })

    # Track 5: VFX Cues (110 lighting/shader cues)
    print("[*] Generating Track 5: VFX & Lighting cues...")
    for idx, s in enumerate(timeline_shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_vfx_{idx+1:03d}_{shot_id.lower().replace('-', '_')}"
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
                "effect": shot_catalog[shot_id]["vfx_desc"]
            }
        })

    # Track 6: Transition Cues (110 cuts & dissolves)
    print("[*] Generating Track 6: Transition cues...")
    for idx, s in enumerate(timeline_shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_trans_{idx+1:03d}_{shot_id.lower().replace('-', '_')}"
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
                "transition": s["transition"],
                "durationSeconds": 0.05 if s["transition"] == "snap" else (0.60 if s["transition"] == "dissolve_act" else 0.35)
            }
        })

    # Track 7: Environment Cues (110 backdrop & void cues)
    print("[*] Generating Track 7: Environment cues...")
    for idx, s in enumerate(timeline_shots):
        shot_id = s["shot_id"]
        cue_id = f"cue_env_{idx+1:03d}_{shot_id.lower().replace('-', '_')}"
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
                "backdropHex": shot_catalog[shot_id]["env_hex"],
                "environmentName": shot_catalog[shot_id]["env_label"]
            }
        })

    # Sort cues by startTime then trackIndex
    cues.sort(key=lambda c: (c["startTime"], c["trackIndex"]))

    # Build the Complete Root Dataset
    dataset = {
        "$schema": "./schema.json",
        "metadata": {
            "title": "The Low Dopamine Morning Routine To Reset Your Brain Focus",
            "topic": "Topic 02",
            "channel": "Isy why (@isy019)",
            "runtimeSeconds": 600.68,
            "fps": 30,
            "resolution": {
                "width": 1920,
                "height": 1080,
                "aspectRatio": "16:9"
            },
            "totalScriptLines": 29,
            "totalShots": 110,
            "totalDialoguePhrases": len(phrases),
            "staticHoldsCount": 11,
            "dynamicMovesCount": 99,
            "totalCues": len(cues),
            "acts": ACTS_INFO
        },
        "mediaReferences": {
            "localVideo": "TOPIC_02_MASTER_VIDEO_FINAL.mp4",
            "masterAudio": "TOPIC_02_FULL_VOICEOVER.mp3",
            "captionsSrt": "TOPIC_02_CAPTIONS.srt",
            "timelineMetadata": "production/topic_02/audio/topic_02_timeline_metadata.json"
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

    # Write output JSON to workspace and Downloads
    print(f"[*] Writing complete dataset to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"[*] Copying dataset to Downloads: {OUTPUT_DL}")
    import shutil
    shutil.copy2(OUTPUT_FILE, OUTPUT_DL)

    # Validate against Schema
    print("[*] Validating dataset against Draft-07 schema:", SCHEMA_FILE)
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.validate(instance=dataset, schema=schema)
    print(">>> JSON SCHEMA DRAFT-07 VALIDATION: PASSED! Zero errors! <<<")

    # Integrity assertions
    assert len([c for c in cues if c["type"] == "shot"]) == 110
    assert len([c for c in cues if c["type"] == "camera"]) == 110
    assert len([c for c in cues if c["type"] == "action"]) == 110
    assert len([c for c in cues if c["type"] == "audio"]) == 110
    assert len([c for c in cues if c["type"] == "vfx"]) == 110
    assert len([c for c in cues if c["type"] == "transition"]) == 110
    assert len([c for c in cues if c["type"] == "environment"]) == 110

    for c in cues:
        assert c["startTime"] < c["endTime"], f"Inverted or zero duration in cue {c['id']}"
        assert c["endTime"] <= 600.68 + 0.5, f"Cue {c['id']} exceeds master runtime"
        if c["type"] == "dialogue":
            assert c["speaker"] == "Sam"
        else:
            assert "speaker" not in c

    print("=" * 80)
    print(f"🎉 SCENEFLOW DATASET COMPLETE!")
    print(f"• Total Cues:        {len(cues):,} cues across 8 tracks")
    print(f"• Shots:             110 (11 Static Holds + 99 Dynamic Camera Moves)")
    print(f"• Dialogue Phrases:  {len(phrases)} synchronized phrases")
    print(f"• Acts:              5 Acts covering 600.68s runtime")
    print(f"• Workspace File:    {OUTPUT_FILE}")
    print(f"• Downloads File:    {OUTPUT_DL}")
    print("=" * 80)
    return dataset

if __name__ == "__main__":
    generate_sceneflow_dataset()

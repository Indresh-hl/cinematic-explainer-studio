import os
import json
import glob
import numpy as np
from PIL import Image

def analyze_shot_positions():
    base_dir = os.path.abspath(".")
    shots_file = os.path.join(base_dir, "assets", "all_timeline_shots.json")
    with open(shots_file, "r") as f:
        shots = json.load(f)
        
    print(f"Analyzing {len(shots)} timeline shots for intelligent text placement...")
    
    # Specific known shot overrides based on storyboard context:
    bed_shots = {
        "LINE_1-B", "LINE_2-B", "LINE_3-A", "LINE_3-B", "LINE_4-A",
        "LINE_13-A", "LINE_13-B", "LINE_14-A", "LINE_14-B", "LINE_15-A", "LINE_15-B",
        "LINE_55-A", "LINE_55-B"
    }
    
    lower_prop_shots = {
        "LINE_1-A", "LINE_5-B", "LINE_9-C", "LINE_12-A", "LINE_17-B", "LINE_21-B",
        "LINE_24-B", "LINE_29-B", "LINE_34-C", "LINE_38-B", "LINE_43-A", "LINE_47-B"
    }
    
    shot_layouts = {}
    target_w, target_h = 1934, 1080
    
    for s in shots:
        name = s["name"]
        if name in shot_layouts:
            continue
            
        cutout_path = os.path.join(base_dir, "assets", "cutouts", f"{name}_cutout.png")
        if not os.path.exists(cutout_path):
            shot_layouts[name] = {"mode": "center", "pos_x": 0.50, "pos_y": 0.22, "type": "unknown"}
            continue
            
        cutout = Image.open(cutout_path).convert("RGBA").resize((target_w, target_h))
        alpha = np.array(cutout.split()[-1])
        
        # Check if bed shot
        if name in bed_shots:
            shot_layouts[name] = {
                "mode": "bed",
                "pos_x": 0.50,
                "pos_y": 0.06,  # Upper dark wall above headboard
                "type": "bed"
            }
            continue
            
        # Check overall subject presence
        char_ratio = np.mean(alpha > 50)
        
        if char_ratio < 0.02:
            # Prop / landscape shot
            if name in lower_prop_shots:
                shot_layouts[name] = {"mode": "center", "pos_x": 0.50, "pos_y": 0.76, "type": "lower_prop"}
            else:
                shot_layouts[name] = {"mode": "center", "pos_x": 0.50, "pos_y": 0.20, "type": "upper_prop"}
            continue
            
        # Analyze subject position in upper/middle reading zone (y = 15% to 60%)
        zone_alpha = alpha[int(target_h * 0.15) : int(target_h * 0.60), :]
        col_density = (zone_alpha > 50).sum(axis=0)
        
        if col_density.max() == 0:
            # Subject is below reading zone
            shot_layouts[name] = {"mode": "center", "pos_x": 0.50, "pos_y": 0.16, "type": "low_subject"}
            continue
            
        active_cols = np.where(col_density > 0.08 * col_density.max())[0]
        char_left = active_cols[0] / target_w
        char_right = active_cols[-1] / target_w
        char_center = (char_left + char_right) / 2
        char_width = char_right - char_left
        
        # DECISION LOGIC ADDRESSING USER FEEDBACK:
        # "A few of the texts or subtitles that you are generating are behind the character fully.
        #  In those cases put it towards the left or write it properly and align it."
        
        # If character is in center (char_left < 0.55 and char_right > 0.45)
        if char_left < 0.55 and char_right > 0.45:
            # Character is centered! Placing text at center (0.50) occludes it!
            # Solution: Put it towards the LEFT!
            shot_layouts[name] = {
                "mode": "left",
                "pos_x": 0.08,   # 8% left margin (~155px)
                "pos_y": 0.24,   # eye/shoulder height beside head
                "type": f"centered_char (w={char_width:.2f})"
            }
        elif char_center < 0.45:
            # Character is on LEFT -> text goes to RIGHT
            shot_layouts[name] = {
                "mode": "right",
                "pos_x": 0.52,   # Right half
                "pos_y": 0.24,
                "type": f"left_char (c={char_center:.2f})"
            }
        else:
            # Character is on RIGHT -> text goes to LEFT
            shot_layouts[name] = {
                "mode": "left",
                "pos_x": 0.08,   # Left margin
                "pos_y": 0.24,
                "type": f"right_char (c={char_center:.2f})"
            }
            
    print("\nShot layout mapping summary:")
    modes = {}
    for k, v in shot_layouts.items():
        modes[v["mode"]] = modes.get(v["mode"], 0) + 1
    print("Mode counts:", modes)
    
    with open("assets/shot_layouts.json", "w") as f:
        json.dump(shot_layouts, f, indent=2)
        
    print("Saved assets/shot_layouts.json successfully!")

if __name__ == "__main__":
    analyze_shot_positions()

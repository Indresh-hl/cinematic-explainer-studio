import cv2
import os
import glob
import json
import numpy as np
import time
import sys

def scan_cuts():
    video_path = r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\0924.mp4"
    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    print("=" * 75)
    print("SCANNING SCENE CUTS ON MASTER TIMELINE VIDEO (0924.mp4)")
    print("=" * 75)
    print(f"Video: {video_path}")
    print(f"FPS: {fps}, Total Frames: {total_frames}, Duration: {duration:.2f}s ({duration/60:.2f}m)")
    sys.stdout.flush()

    # Load all 180 cleaned image thumbnails for Topic 02
    cleaned_files = sorted(glob.glob("production/topic_02/images/cleaned/*.jpeg"))
    thumbs = []
    names = []
    for f in cleaned_files:
        name = os.path.splitext(os.path.basename(f))[0]
        im = cv2.imread(f)
        if im is not None:
            thumbs.append(cv2.resize(im, (160, 90)))
            names.append(name)

    print(f"Loaded {len(thumbs)} cleaned reference thumbnails.")
    sys.stdout.flush()

    t0 = time.time()
    step = 6  # check every 6 frames (5 times per second)
    timeline_cuts = []
    prev_name = None

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx % step == 0:
            small = cv2.resize(frame, (160, 90))
            diffs = [np.mean(cv2.absdiff(small, th)) for th in thumbs]
            best_idx = int(np.argmin(diffs))
            best_name = names[best_idx]
            
            if best_name != prev_name:
                t = frame_idx / fps
                timeline_cuts.append({
                    "frame": frame_idx,
                    "time": round(t, 2),
                    "name": best_name,
                    "diff": round(float(diffs[best_idx]), 2)
                })
                prev_name = best_name
                
        if frame_idx % 1500 == 0:
            pct = frame_idx / total_frames * 100
            print(f"  [Scan] Frame {frame_idx}/{total_frames} ({pct:.1f}%) | Time: {frame_idx/fps:.1f}s | Cuts detected: {len(timeline_cuts)}")
            sys.stdout.flush()

        frame_idx += 1

    cap.release()
    print(f"\nSequential scan finished in {time.time() - t0:.1f}s. Total raw transitions: {len(timeline_cuts)}")
    sys.stdout.flush()

    # Filter glitches (< 0.4s)
    cleaned_shots = []
    for i, c in enumerate(timeline_cuts):
        start_t = c["time"]
        end_t = timeline_cuts[i+1]["time"] if i + 1 < len(timeline_cuts) else round(duration, 2)
        dur = round(end_t - start_t, 2)
        if dur >= 0.4 or i == len(timeline_cuts) - 1:
            cleaned_shots.append({
                "name": c["name"],
                "start": start_t,
                "end": end_t,
                "duration": dur,
                "frame": c["frame"]
            })

    # Merge consecutive identical shots
    final_shots = []
    for s in cleaned_shots:
        if final_shots and final_shots[-1]["name"] == s["name"]:
            final_shots[-1]["end"] = s["end"]
            final_shots[-1]["duration"] = round(final_shots[-1]["end"] - final_shots[-1]["start"], 2)
        else:
            final_shots.append(s)

    # Re-link contiguous start and end times
    for i in range(len(final_shots)):
        if i > 0:
            final_shots[i]["start"] = final_shots[i-1]["end"]
        if i + 1 < len(final_shots):
            final_shots[i]["end"] = final_shots[i+1]["start"]
        else:
            final_shots[i]["end"] = round(duration, 2)
        final_shots[i]["duration"] = round(final_shots[i]["end"] - final_shots[i]["start"], 2)

    os.makedirs("production/topic_02", exist_ok=True)
    out_json = "production/topic_02/all_timeline_shots.json"
    with open(out_json, "w") as f:
        json.dump(final_shots, f, indent=2)

    print(f"\n[SUCCESS] Final unified shots mapped: {len(final_shots)}")
    print("First 5 shots:")
    for s in final_shots[:5]:
        print(f"  {s['name']}: {s['start']}s -> {s['end']}s ({s['duration']}s)")
    print("Last 5 shots:")
    for s in final_shots[-5:]:
        print(f"  {s['name']}: {s['start']}s -> {s['end']}s ({s['duration']}s)")

if __name__ == "__main__":
    scan_cuts()

import cv2
import numpy as np
import json

video_path = r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\0922 (1).mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

max_sec = 46.0
max_frames = int(max_sec * fps)

prev_frame = None
cuts = [0.0]

for f_idx in range(max_frames):
    ret, frame = cap.read()
    if not ret:
        break
        
    # Downscale and gray for scene change detection
    gray = cv2.cvtColor(cv2.resize(frame, (160, 90)), cv2.COLOR_BGR2GRAY)
    if prev_frame is not None:
        diff = np.mean(cv2.absdiff(gray, prev_frame))
        # Hard cuts have a diff of > 10.0
        if diff > 10.0:
            t = round(f_idx / fps, 3)
            if t - cuts[-1] > 0.4:
                cuts.append(t)
    prev_frame = gray

cap.release()

print(f"Detected {len(cuts)} exact cut points in 0 to {max_sec}s:")
for i, c in enumerate(cuts):
    print(f"  Shot {i+1}: {c}s")

with open("assets/act1_exact_cuts.json", "w") as f:
    json.dump(cuts, f, indent=2)

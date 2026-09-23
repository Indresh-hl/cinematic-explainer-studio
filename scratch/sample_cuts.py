import cv2
import numpy as np
import json

video_path = r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\0922 (1).mp4"
cap = cv2.VideoCapture(video_path)

cuts = []
prev_img = None
max_time = 75.0 # Check first 75 seconds

t = 0.0
step = 0.25 # check every 250ms

while t <= max_time:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ret, frame = cap.read()
    if not ret:
        break
        
    small = cv2.resize(frame, (160, 90))
    if prev_img is not None:
        diff = np.mean(cv2.absdiff(small, prev_img))
        if diff > 15.0:
            cuts.append({"time": round(t, 2), "diff": round(diff, 1)})
    else:
        cuts.append({"time": 0.0, "diff": 0.0})
        
    prev_img = small
    t += step

cap.release()

print(f"Detected {len(cuts)} shot transitions in 0 to {max_time}s:")
for c in cuts:
    print(f"  Shot at {c['time']:0.2f}s (diff: {c['diff']})")

with open("assets/act1_sampled_cuts.json", "w") as f:
    json.dump(cuts, f, indent=2)

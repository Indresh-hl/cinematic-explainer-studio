import cv2
import numpy as np

video_path = r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\0922 (1).mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

print(f"FPS: {fps}")
frame_count = int(75 * fps) # First 75 seconds

prev_small = None
cut_times = [0.0]

for f_idx in range(frame_count):
    ret, frame = cap.read()
    if not ret:
        break
        
    small = cv2.resize(frame, (80, 45))
    if prev_small is not None:
        diff = np.mean(cv2.absdiff(small, prev_small))
        if diff > 18.0:
            t = round(f_idx / fps, 2)
            if t - cut_times[-1] > 0.6:
                cut_times.append(t)
    prev_small = small

cap.release()

print(f"Detected {len(cut_times)} shots in first 75 seconds:")
for idx, ct in enumerate(cut_times):
    print(f"  Shot {idx+1}: {ct}s")

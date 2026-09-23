import cv2
import json

video_path = r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\0922 (1).mp4"
cap = cv2.VideoCapture(video_path)

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps

print(f"Video: {video_path}")
print(f"FPS: {fps}, Total Frames: {total_frames}, Duration: {duration:.2f}s ({duration/60:.2f}m)")

# Sample first 20 cuts
cuts = []
prev_frame = None
frame_idx = 0

step = 3 # Sample every 3 frames for speed (10 checks per second)
cuts.append({"frame": 0, "time": 0.0})

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    if frame_idx % step == 0:
        small = cv2.resize(frame, (160, 90))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        if prev_frame is not None:
            diff = cv2.absdiff(gray, prev_frame).mean()
            # If significant visual change between scenes
            if diff > 22.0:
                cut_time = round(frame_idx / fps, 2)
                # Avoid registering cuts too close to each other (<0.5s)
                if not cuts or (cut_time - cuts[-1]["time"] >= 0.8):
                    cuts.append({"frame": frame_idx, "time": cut_time, "diff": round(diff, 1)})
        prev_frame = gray
        
    frame_idx += 1

cap.release()

print(f"\nTotal scene cuts detected: {len(cuts)}")
print("\nFirst 15 scene cuts:")
for c in cuts[:15]:
    print(f"  Shot at {c['time']}s (Frame {c['frame']})")

with open("assets/detected_timeline_cuts.json", "w") as f:
    json.dump(cuts, f, indent=2)

print("\nSaved assets/detected_timeline_cuts.json successfully!")

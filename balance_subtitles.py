import re

for p in [r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\0922 (1).srt", r"c:\Users\Indresh HL\Downloads\youtube long fromat\captions.srt"]:
    with open(p, "r", encoding="utf-8") as f:
        blocks = f.read().strip().split("\n\n")
    
    parsed = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) >= 3:
            idx = lines[0]
            times = lines[1]
            text = " ".join(lines[2:])
            start, end = times.split(" --> ")
            parsed.append({"start": start, "end": end, "text": text})

    merged = []
    for item in parsed:
        if not merged:
            merged.append(item)
            continue
        prev = merged[-1]
        prev_words = prev["text"].split()
        curr_words = item["text"].split()

        # If curr has <= 2 words and total words <= 9, merge into prev
        if len(curr_words) <= 2 and len(prev_words) + len(curr_words) <= 9:
            prev["end"] = item["end"]
            prev["text"] = prev["text"] + " " + item["text"]
        elif len(prev_words) <= 2 and len(prev_words) + len(curr_words) <= 9:
            prev["end"] = item["end"]
            prev["text"] = prev["text"] + " " + item["text"]
        else:
            merged.append(item)

    out = []
    for i, item in enumerate(merged, 1):
        s = item["start"]
        e = item["end"]
        t = item["text"]
        out.append(f"{i}\n{s} --> {e}\n{t}")
    
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out) + "\n")

    print(f"Polished {p}: from {len(parsed)} to {len(merged)} balanced cards.")

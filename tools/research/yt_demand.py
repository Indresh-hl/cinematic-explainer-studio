#!/usr/bin/env python3
"""
Free YouTube demand check for NeuroSync topic research (no API key, no cost).

For each seed query it collects:
  1. YouTube autocomplete suggestions  -> what people actually type
  2. Top search results with view counts, channel and age -> proven demand + competition

Usage:
    python yt_demand.py "why do i procrastinate" "dopamine detox" --out ../../production/research/procrastination.md

The Markdown output is meant to be pasted into / read by the research phase of the skill.
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def autocomplete(q):
    url = "https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q=" + urllib.parse.quote(q)
    try:
        return json.loads(fetch(url))[1]
    except Exception as e:  # network hiccup should not kill the whole run
        return [f"(autocomplete failed: {e})"]


def walk(o, key):
    if isinstance(o, dict):
        if key in o:
            yield o[key]
        for v in o.values():
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, key)


def text(t):
    if not t:
        return ""
    return t.get("simpleText") or "".join(r.get("text", "") for r in t.get("runs", []))


def parse_views(s):
    m = re.search(r"([\d.,]+)\s*([KMB]?)", s.replace(",", ""))
    if not m:
        return 0
    n = float(m.group(1))
    return int(n * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2)])


def search(q, limit):
    # sp=EgIQAQ%3D%3D filters to videos only
    html = fetch("https://www.youtube.com/results?sp=EgIQAQ%253D%253D&search_query=" + urllib.parse.quote(q))
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if not m:
        return []
    out = []
    for v in walk(json.loads(m.group(1)), "videoRenderer"):
        views_txt = text(v.get("viewCountText"))
        out.append({
            "title": text(v.get("title")),
            "channel": text(v.get("ownerText")),
            "views": parse_views(views_txt),
            "views_txt": views_txt,
            "age": text(v.get("publishedTimeText")),
            "length": text(v.get("lengthText")),
            "url": "https://youtu.be/" + v.get("videoId", ""),
        })
        if len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--out")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    lines = [f"# YouTube demand check ({date.today().isoformat()})", ""]
    for q in a.queries:
        sugg = autocomplete(q)
        res = search(q, a.limit)
        views = sorted((r["views"] for r in res), reverse=True)
        median = views[len(views) // 2] if views else 0
        lines += [f"## Query: `{q}`", "",
                  "**Autocomplete (what people type):** " + "; ".join(sugg[:10]), "",
                  f"**Top {len(res)} results** - median views: {median:,}", "",
                  "| # | Views | Age | Length | Channel | Title |", "|---|---|---|---|---|---|"]
        for i, r in enumerate(res, 1):
            title = r["title"].replace("|", "/")
            lines.append(f"| {i} | {r['views']:,} | {r['age']} | {r['length']} | {r['channel']} | [{title}]({r['url']}) |")
        lines.append("")
    md = "\n".join(lines)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(md, encoding="utf-8")
        print(f"Saved {a.out}")
    print(md)


if __name__ == "__main__":
    main()

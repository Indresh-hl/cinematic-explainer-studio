#!/usr/bin/env python3
"""
Bulk rebrand an existing YouTube channel (old name: "Isy why" / ISYY / @isy019).

Commands (run from this folder):
    python rebrand_channel.py auth                 # one-time Google login (OAuth)
    python rebrand_channel.py scan                 # DRY RUN: find old-brand videos, write preview + backup
    python rebrand_channel.py scan --all-videos    # also standardise tags/hashtags on videos without the old name
    python rebrand_channel.py apply [--limit N]    # push the previewed changes to YouTube
    python rebrand_channel.py banner               # upload the new 4K banner
    python rebrand_channel.py channel              # update channel description + channel keywords
    python rebrand_channel.py rollback BACKUP.json # restore original titles/descriptions/tags

Why OAuth and not an API key: a YouTube API key can only READ public data.
Editing videos, the banner, or channel settings requires OAuth consent from the channel owner.

Quota (default 10,000 units/day): videos.update = 50 units -> about 190 video edits per day.
`apply` saves progress, so if the quota runs out just run it again the next day.
"""
import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "rebrand_output"
CONFIG_PATH = HERE / "rebrand_config.json"
TOKEN_PATH = HERE / "token.json"
CLIENT_SECRET_PATH = HERE / "client_secret.json"
PREVIEW_PATH = OUT / "preview.json"
APPLIED_PATH = OUT / "applied.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

TITLE_MAX = 100
DESCRIPTION_MAX = 5000
BANNER_MAX_BYTES = 6 * 1024 * 1024
CHANNEL_KEYWORDS_MAX = 500


# --------------------------------------------------------------------------- config

def load_config():
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    placeholders = [k for k in ("new_channel_name", "new_handle", "brand_hashtag")
                    if "YOUR_NEW" in cfg.get(k, "") or "YourNew" in cfg.get(k, "")]
    if placeholders:
        sys.exit(f"[config] Fill in {', '.join(placeholders)} in {CONFIG_PATH.name} first.")
    if not cfg["new_handle"].startswith("@"):
        cfg["new_handle"] = "@" + cfg["new_handle"]
    if not cfg["brand_hashtag"].startswith("#"):
        cfg["brand_hashtag"] = "#" + cfg["brand_hashtag"]
    if " " in cfg["brand_hashtag"]:
        sys.exit("[config] brand_hashtag cannot contain spaces.")
    subs = {
        "name": cfg["new_channel_name"],
        "handle": cfg["new_handle"],
        "handle_bare": cfg["new_handle"].lstrip("@"),
        "hashtag": cfg["brand_hashtag"],
    }
    cfg["_rules"] = [(re.compile(r["pattern"], re.IGNORECASE), r["replace_with"].format(**subs))
                     for r in cfg["replacements"]]
    return cfg


# --------------------------------------------------------------------------- transforms (pure, testable)

def has_old_brand(text, cfg):
    return any(rx.search(text or "") for rx, _ in cfg["_rules"])


def replace_old_brand(text, cfg):
    for rx, repl in cfg["_rules"]:
        text = rx.sub(repl, text)
    return text


def tags_length(tags):
    # YouTube counts quotes around multi-word tags plus the separating commas.
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + max(len(tags) - 1, 0)


def transform_tags(tags, cfg):
    out, seen = [], set()

    def add(tag):
        tag = re.sub(r"[<>,]", "", tag or "").strip()
        if not tag or tag.lower() in seen:
            return
        if tags_length(out + [tag]) > cfg["max_tag_chars"]:
            return
        seen.add(tag.lower())
        out.append(tag)

    add(cfg["new_channel_name"])
    for tag in tags or []:
        if has_old_brand(tag, cfg):
            continue  # old brand tag dropped; new brand tag already added
        add(tag)
    for tag in cfg["standard_tags"]:
        add(tag)
    return out


def transform_title(title, cfg):
    new = re.sub(r"\s{2,}", " ", replace_old_brand(title, cfg)).strip()
    new = new.replace("<", "").replace(">", "")
    warning = None
    if len(new) > TITLE_MAX:
        new = new[:TITLE_MAX].rsplit(" ", 1)[0]
        warning = "title trimmed to 100 chars"
    return new, warning


def transform_description(desc, cfg):
    new = replace_old_brand(desc or "", cfg)
    # drop internal production notes block ("ART DIRECTION & PRODUCTION" ... up to hashtags / end)
    new = re.sub(r"\n*[^\n]*ART DIRECTION[^\n]*\n(?:[\u2022\-][^\n]*\n?)+", "\n\n", new, flags=re.IGNORECASE)
    new = re.sub(r"(\n\s*\u2501+\s*)+(?=\n\s*#|\s*$)", "\n", new)  # dangling divider lines
    # de-duplicate hashtags (case-insensitive) while keeping order
    seen_tags = set()

    def dedupe(m):
        k = m.group(0).lower()
        if k in seen_tags:
            return ""
        seen_tags.add(k)
        return m.group(0)
    new = re.sub(r"(?<![\w&])#\w+", dedupe, new)
    new = re.sub(r"[ \t]{2,}", " ", new)
    new = re.sub(r"\n{3,}", "\n\n", new).strip()
    existing = re.findall(r"(?<![\w&])#\w+", new)
    existing_lower = {h.lower() for h in existing}
    wanted = [cfg["brand_hashtag"]] + cfg["standard_hashtags"]
    room = max(cfg["max_hashtags"] - len(existing), 0)
    missing = [h for h in wanted if h.lower() not in existing_lower][:room]
    needs_more = len(existing) < cfg["min_hashtags"] or cfg["brand_hashtag"].lower() not in existing_lower
    if needs_more and missing:
        new = new.rstrip() + "\n\n" + " ".join(missing)
    new = new.replace("<", "\u2039").replace(">", "\u203a")  # YouTube rejects < and >
    warning = None
    if len(new) > DESCRIPTION_MAX:
        new = new[:DESCRIPTION_MAX]
        warning = "description trimmed to 5000 chars"
    return new, warning


def plan_video(video, cfg, all_videos=False):
    sn = video["snippet"]
    title, desc, tags = sn.get("title", ""), sn.get("description", ""), sn.get("tags", [])
    matched = has_old_brand(title, cfg) or has_old_brand(desc, cfg) or any(has_old_brand(t, cfg) for t in tags)
    if not matched and not all_videos:
        return None
    new_title, w1 = transform_title(title, cfg)
    new_desc, w2 = transform_description(desc, cfg)
    new_tags = transform_tags(tags, cfg)
    if new_title == title and new_desc == desc and new_tags == tags:
        return None
    return {
        "id": video["id"],
        "url": f"https://youtu.be/{video['id']}",
        "privacy": video.get("status", {}).get("privacyStatus", ""),
        "matched_old_brand": matched,
        "categoryId": sn.get("categoryId", "27"),
        "defaultLanguage": sn.get("defaultLanguage"),
        "defaultAudioLanguage": sn.get("defaultAudioLanguage"),
        "old": {"title": title, "description": desc, "tags": tags},
        "new": {"title": new_title, "description": new_desc, "tags": new_tags},
        "warnings": [w for w in (w1, w2) if w],
    }


# --------------------------------------------------------------------------- YouTube API

def youtube_client():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit("Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_PATH.exists():
                sys.exit(f"Missing {CLIENT_SECRET_PATH.name}. Download the OAuth 'Desktop app' client JSON "
                         "from Google Cloud Console and save it in this folder with that exact name.")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent")
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def my_channel(yt, parts="snippet,contentDetails,brandingSettings"):
    items = yt.channels().list(part=parts, mine=True).execute().get("items", [])
    if not items:
        sys.exit("This Google account has no YouTube channel. Log in with the channel's account (or Brand Account).")
    return items[0]


def all_uploads(yt, channel):
    playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=playlist,
                                    maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    videos = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,status", id=",".join(ids[i:i + 50])).execute()
        videos += r.get("items", [])
    return videos


def is_quota_error(err):
    return getattr(err, "resp", None) is not None and err.resp.status == 403 and b"quota" in (err.content or b"").lower()


# --------------------------------------------------------------------------- commands

def cmd_auth(_args):
    ch = my_channel(youtube_client(), "snippet")
    print(f"Authorized for channel: {ch['snippet']['title']}  ({ch['id']})")


def cmd_scan(args):
    cfg = load_config()
    yt = youtube_client()
    ch = my_channel(yt)
    print(f"Channel: {ch['snippet']['title']} ({ch['id']}) - fetching every upload...")
    videos = all_uploads(yt, ch)
    OUT.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = OUT / f"backup_{stamp}.json"
    backup.write_text(json.dumps(videos, indent=2, ensure_ascii=False), encoding="utf-8")

    plans = [p for p in (plan_video(v, cfg, args.all_videos) for v in videos) if p]
    PREVIEW_PATH.write_text(json.dumps({"backup": backup.name, "channel_id": ch["id"], "plans": plans},
                                       indent=2, ensure_ascii=False), encoding="utf-8")
    with open(OUT / "preview.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["video_id", "url", "privacy", "old_brand_found", "old_title", "new_title",
                    "old_tags", "new_tags", "warnings"])
        for p in plans:
            w.writerow([p["id"], p["url"], p["privacy"], p["matched_old_brand"], p["old"]["title"],
                        p["new"]["title"], ", ".join(p["old"]["tags"]), ", ".join(p["new"]["tags"]),
                        "; ".join(p["warnings"])])

    matched = sum(p["matched_old_brand"] for p in plans)
    print(f"\nTotal uploads: {len(videos)} | old brand found in: {matched} | videos to update: {len(plans)}")
    print(f"Estimated quota for apply: {len(plans) * 50} units (daily default 10,000)")
    print(f"Backup of ALL original metadata : {backup}")
    print(f"Review before applying          : {OUT / 'preview.csv'}  (full text in preview.json)")
    print("Nothing was changed on YouTube. Run `python rebrand_channel.py apply` when happy.")


def cmd_apply(args):
    from googleapiclient.errors import HttpError
    if not PREVIEW_PATH.exists():
        sys.exit("Run `scan` first.")
    preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
    applied = set(json.loads(APPLIED_PATH.read_text())) if APPLIED_PATH.exists() else set()
    todo = [p for p in preview["plans"] if p["id"] not in applied]
    if args.limit:
        todo = todo[:args.limit]
    if not todo:
        sys.exit("Nothing left to apply.")
    print(f"About to update {len(todo)} videos on YouTube (backup: {preview['backup']}).")
    if not args.yes and input("Type YES to continue: ").strip() != "YES":
        sys.exit("Cancelled.")

    yt = youtube_client()
    done = 0
    for p in todo:
        snippet = {"title": p["new"]["title"], "description": p["new"]["description"],
                   "tags": p["new"]["tags"], "categoryId": p["categoryId"]}
        for key in ("defaultLanguage", "defaultAudioLanguage"):
            if p.get(key):
                snippet[key] = p[key]  # omitted fields get wiped by videos.update
        try:
            yt.videos().update(part="snippet", body={"id": p["id"], "snippet": snippet}).execute()
        except HttpError as e:
            if is_quota_error(e):
                print("Daily quota reached. Progress saved - run `apply` again tomorrow.")
                break
            print(f"  FAILED {p['id']}: {e}")
            continue
        applied.add(p["id"])
        APPLIED_PATH.write_text(json.dumps(sorted(applied)), encoding="utf-8")
        done += 1
        print(f"  [{done}/{len(todo)}] {p['new']['title']}")
        time.sleep(0.3)
    print(f"Updated {done} videos. Total applied so far: {len(applied)}/{len(preview['plans'])}")


def cmd_banner(args):
    from googleapiclient.http import MediaFileUpload
    cfg = load_config()
    path = (HERE / (args.path or cfg["banner_path"])).resolve()
    if not path.exists():
        sys.exit(f"Banner not found: {path}")
    if path.stat().st_size > BANNER_MAX_BYTES:
        sys.exit("Banner must be under 6 MB.")
    yt = youtube_client()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    url = yt.channelBanners().insert(media_body=MediaFileUpload(str(path), mimetype=mime)).execute()["url"]
    ch = my_channel(yt, "brandingSettings")
    bs = ch.get("brandingSettings", {})
    body = {"id": ch["id"], "brandingSettings": {"channel": bs.get("channel", {}),
                                                  "image": {"bannerExternalUrl": url}}}
    yt.channels().update(part="brandingSettings", body=body).execute()
    print(f"Banner uploaded from {path.name}. It can take a few minutes to appear on the channel page.")


def format_channel_keywords(keywords):
    out = []
    for k in keywords:
        token = f'"{k}"' if " " in k else k
        if len(" ".join(out + [token])) > CHANNEL_KEYWORDS_MAX:
            break
        out.append(token)
    return " ".join(out)


def cmd_channel(_args):
    cfg = load_config()
    yt = youtube_client()
    ch = my_channel(yt, "brandingSettings")
    channel = dict(ch.get("brandingSettings", {}).get("channel", {}))
    backup = OUT / f"channel_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    OUT.mkdir(exist_ok=True)
    backup.write_text(json.dumps(channel, indent=2, ensure_ascii=False), encoding="utf-8")
    channel["description"] = replace_old_brand(cfg["channel_description"], cfg)[:1000]
    channel["keywords"] = format_channel_keywords(cfg["channel_keywords"] + [cfg["new_channel_name"]])
    channel.pop("title", None)  # channel name can only be changed in YouTube Studio
    yt.channels().update(part="brandingSettings", body={"id": ch["id"], "brandingSettings": {"channel": channel}}).execute()
    print(f"Channel description + keywords updated. Old values saved to {backup}")


def cmd_rollback(args):
    from googleapiclient.errors import HttpError
    backup = Path(args.backup)
    if not backup.is_absolute():
        backup = OUT / backup
    originals = {v["id"]: v["snippet"] for v in json.loads(backup.read_text(encoding="utf-8"))}
    applied = json.loads(APPLIED_PATH.read_text()) if APPLIED_PATH.exists() else []
    print(f"Restoring {len(applied)} videos from {backup.name}")
    if input("Type YES to continue: ").strip() != "YES":
        sys.exit("Cancelled.")
    yt = youtube_client()
    for vid in list(applied):
        sn = originals.get(vid)
        if not sn:
            continue
        snippet = {k: sn[k] for k in ("title", "description", "tags", "categoryId",
                                      "defaultLanguage", "defaultAudioLanguage") if k in sn}
        try:
            yt.videos().update(part="snippet", body={"id": vid, "snippet": snippet}).execute()
            applied.remove(vid)
            APPLIED_PATH.write_text(json.dumps(applied), encoding="utf-8")
            print(f"  restored {vid}")
        except HttpError as e:
            if is_quota_error(e):
                print("Daily quota reached. Run rollback again tomorrow.")
                break
            print(f"  FAILED {vid}: {e}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    s = sub.add_parser("scan")
    s.add_argument("--all-videos", action="store_true", help="also standardise tags/hashtags on every video")
    a = sub.add_parser("apply")
    a.add_argument("--limit", type=int, default=0)
    a.add_argument("--yes", action="store_true")
    b = sub.add_parser("banner")
    b.add_argument("--path", help="override banner_path from config")
    sub.add_parser("channel")
    r = sub.add_parser("rollback")
    r.add_argument("backup")
    args = ap.parse_args()
    {"auth": cmd_auth, "scan": cmd_scan, "apply": cmd_apply, "banner": cmd_banner,
     "channel": cmd_channel, "rollback": cmd_rollback}[args.cmd](args)


if __name__ == "__main__":
    main()

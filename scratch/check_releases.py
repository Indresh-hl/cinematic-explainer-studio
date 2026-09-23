import urllib.request, json
url = "https://api.github.com/repos/xinntao/Real-ESRGAN/releases"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        for r in data[:5]:
            print("Release:", r.get("tag_name"))
            for a in r.get("assets", []):
                name = a.get("name", "")
                if "windows" in name.lower() or "zip" in name.lower():
                    print("  ", name, a.get("browser_download_url"))
except Exception as e:
    print("Error:", e)

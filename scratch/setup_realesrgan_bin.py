import urllib.request
import zipfile
import os

os.makedirs("tools", exist_ok=True)
url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
zip_path = "tools/realesrgan-windows.zip"

print(f"Downloading {url}...")
urllib.request.urlretrieve(url, zip_path)
print("Downloaded! Extracting...")

with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall("tools/realesrgan")

print("Extracted to tools/realesrgan!")
exe_path = "tools/realesrgan/realesrgan-ncnn-vulkan.exe"
print("Exists:", os.path.exists(exe_path))

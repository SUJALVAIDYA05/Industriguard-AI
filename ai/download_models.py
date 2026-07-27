"""
Download required YOLO model files for IndustriGuard AI.
Run this once when internet is available.
"""
import os
import sys
from pathlib import Path

MODELS = {
    "ppe_model.pt": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt",
    "ppe_model_v8.pt": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt",
    "yolo11n.pt": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt",
}

AI_DIR = Path(__file__).parent

def check_connectivity():
    import socket
    try:
        socket.create_connection(("github.com", 443), timeout=3)
        return True
    except OSError:
        return False

def download_file(url, dest):
    import requests
    print(f"Downloading {dest.name} ...")
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    downloaded = 0
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = int(100 * downloaded / total)
                print(f"\r  {pct}% ({downloaded//1024}KB / {total//1024}KB)", end="")
    print(f"\n  Saved to {dest}")

def main():
    if not check_connectivity():
        print("No internet connectivity detected.")
        print("Please connect to the internet and re-run this script.")
        print("Alternatively, manually download the model file and place it in:")
        print(f"  {AI_DIR}")
        sys.exit(1)

    model_name = sys.argv[1] if len(sys.argv) > 1 else "ppe_model.pt"
    if model_name not in MODELS:
        print(f"Unknown model '{model_name}'. Available: {list(MODELS.keys())}")
        sys.exit(1)

    dest = AI_DIR / model_name
    if dest.exists():
        print(f"{model_name} already exists at {dest}")
        return

    download_file(MODELS[model_name], dest)
    print("Done.")

if __name__ == "__main__":
    main()

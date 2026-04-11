from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]
URL_FILE = PROJECT_ROOT / "data" / "metadata" / "stuttering_urls.txt"
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "stuttering"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def read_urls(file_path: Path):
    urls = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls

def download_audio(url: str):
    command = [
        "yt-dlp",
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", str(OUTPUT_DIR / "%(id)s.%(ext)s"),
        url
    ]

    try:
        subprocess.run(command, check=True)
        print(f"[OK] Downloaded: {url}")
    except subprocess.CalledProcessError:
        print(f"[ERROR] Failed: {url}")

def main():
    print(f"[INFO] URL file: {URL_FILE}")
    print(f"[INFO] Output dir: {OUTPUT_DIR}")

    if not URL_FILE.exists():
        print("[ERROR] URL file not found.")
        return

    urls = read_urls(URL_FILE)
    print(f"[INFO] Found {len(urls)} URLs.")

    if not urls:
        print("[WARNING] No URLs found.")
        return

    for url in urls:
        download_audio(url)

if __name__ == "__main__":
    main()
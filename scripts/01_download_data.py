from pathlib import Path
import subprocess
from urllib.parse import urlparse, parse_qs

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Burda Dosya dizini kendinize göre ayarlanacaktır örnek stuttering yerine kendi hastalığınızın adını yazabilirsiniz


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


def extract_video_id(url: str):
    parsed = urlparse(url)
    return parse_qs(parsed.query).get("v", [None])[0]


def already_downloaded(video_id: str) -> bool:
    if video_id is None:
        return False
    exts = [".wav", ".mp3", ".m4a", ".webm", ".ogg", ".opus", ".mp4"]
    return any((OUTPUT_DIR / f"{video_id}{ext}").exists() for ext in exts)


def download_audio(url: str):
    video_id = extract_video_id(url)

    if already_downloaded(video_id):
        print(f"[SKIP] Already downloaded: {video_id}")
        return

    command = [
        "yt-dlp",
        "--no-playlist",
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
    if not URL_FILE.exists():
        print(f"[ERROR] URL file not found: {URL_FILE}")
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
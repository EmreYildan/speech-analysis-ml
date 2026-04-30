from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "scarpinged_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 🔑 YOU control this list — no URLs, only keywords
SEARCH_KEYWORDS = [
    "stuttering interview adult",
    "person with stutter speaking",
    "mild stuttering speech example",
    "severe stuttering speech",
    "stammering conversation real life",
    "speech disorder stuttering example",
    "kekeme konuşma örneği",
    "kekemelik röportaj",
    "stuttering short video",
    "stutter vlog speaking",
]
print(OUTPUT_DIR)


def download_by_search(keyword: str, n_results=1):
    print(f"\n[SEARCH] {keyword}")

    cmd = [
        "yt-dlp",
        f"ytsearch{n_results}:{keyword}",  
        "-f", "bv*+ba/best",
        "--merge-output-format", "mp4",
        "--ignore-errors",
        "--no-playlist",
        "-o", str(OUTPUT_DIR / "%(id)s_%(title).80s.%(ext)s"),
    ]

    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    print(f"[INFO] Saving to: {OUTPUT_DIR}")

    for kw in SEARCH_KEYWORDS:
        download_by_search(kw, n_results=15)  # increase if needed

    print("\n[DONE] Downloads completed.")
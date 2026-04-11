from pathlib import Path
import random
import shutil
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "data" / "interim" / "segmented" / "stuttering"
TRAIN_DIR = PROJECT_ROOT / "data" / "processed" / "train_set" / "stuttering"
TEST_DIR = PROJECT_ROOT / "data" / "processed" / "test_set" / "stuttering"

TRAIN_DIR.mkdir(parents=True, exist_ok=True)
TEST_DIR.mkdir(parents=True, exist_ok=True)

TEST_RATIO = 0.2
SEED = 42


def extract_video_id(filename: str) -> str:
    """
    Example:
    7n3YS7GdQ0k_seg_001.wav -> 7n3YS7GdQ0k
    """
    return filename.split("_seg_")[0]


def clear_directory(folder: Path):
    for f in folder.glob("*.wav"):
        f.unlink()


def main():
    print(f"[INFO] Input dir: {INPUT_DIR}")
    print(f"[INFO] Train dir: {TRAIN_DIR}")
    print(f"[INFO] Test dir: {TEST_DIR}")

    if not INPUT_DIR.exists():
        print("[ERROR] Input directory does not exist.")
        return

    files = list(INPUT_DIR.glob("*.wav"))
    print(f"[INFO] Found {len(files)} segment files.")

    if not files:
        print("[WARNING] No segment files found.")
        return

    # Her çalıştırmada train/test klasörlerini temizle
    clear_directory(TRAIN_DIR)
    clear_directory(TEST_DIR)

    video_to_files = defaultdict(list)
    for f in files:
        video_id = extract_video_id(f.name)
        video_to_files[video_id].append(f)

    video_ids = list(video_to_files.keys())
    print(f"[INFO] Found {len(video_ids)} unique videos.")

    random.seed(SEED)
    random.shuffle(video_ids)

    test_video_count = max(1, int(len(video_ids) * TEST_RATIO))
    test_video_ids = set(video_ids[:test_video_count])
    train_video_ids = set(video_ids[test_video_count:])

    print(f"[INFO] Train videos: {len(train_video_ids)}")
    print(f"[INFO] Test videos: {len(test_video_ids)}")

    train_count = 0
    test_count = 0

    for video_id in train_video_ids:
        for f in video_to_files[video_id]:
            shutil.copy2(f, TRAIN_DIR / f.name)
            train_count += 1

    for video_id in test_video_ids:
        for f in video_to_files[video_id]:
            shutil.copy2(f, TEST_DIR / f.name)
            test_count += 1

    print(f"[OK] Train segments copied: {train_count}")
    print(f"[OK] Test segments copied: {test_count}")

    print("\n[INFO] Test video IDs:")
    for vid in sorted(test_video_ids):
        print(f" - {vid}")

    print("\n[INFO] Train video IDs:")
    for vid in sorted(train_video_ids):
        print(f" - {vid}")


if __name__ == "__main__":
    main()
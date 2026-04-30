from __future__ import annotations

import csv
import random
import shutil
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LABEL = "stuttering"

INPUT_DIR = PROJECT_ROOT / "data" / "interim" / "segmented_clean_relaxed" / LABEL

TRAIN_DIR = PROJECT_ROOT / "data" / "processed" / "train_set" / LABEL
TEST_DIR = PROJECT_ROOT / "data" / "processed" / "test_set" / LABEL

SPLIT_METADATA_CSV = PROJECT_ROOT / "data" / "metadata" / f"{LABEL}_split_metadata.csv"
VIDEO_SPLIT_SUMMARY_CSV = PROJECT_ROOT / "data" / "metadata" / f"{LABEL}_video_split_summary.csv"

TEST_RATIO = 0.20
SEED = 42
N_TRIALS = 50000


def extract_video_id(filename: str) -> str:
    return filename.split("_seg_")[0]


def reset_directory(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)

    for f in folder.glob("*.wav"):
        try:
            f.unlink()
        except PermissionError:
            print(f"[WARN] Permission denied, skipped: {f}")


def choose_test_videos(video_to_files: dict[str, list[Path]]) -> set[str]:
    rng = random.Random(SEED)

    video_ids = sorted(video_to_files.keys())
    total_segments = sum(len(files) for files in video_to_files.values())
    target_test_segments = total_segments * TEST_RATIO

    best_test_videos = None
    best_error = float("inf")

    # En az 1 video testte olsun, ama tüm videolar test olmasın
    for _ in range(N_TRIALS):
        shuffled = video_ids[:]
        rng.shuffle(shuffled)

        chosen = set()
        current_segments = 0

        for vid in shuffled:
            candidate_segments = current_segments + len(video_to_files[vid])

            if abs(candidate_segments - target_test_segments) < abs(current_segments - target_test_segments):
                chosen.add(vid)
                current_segments = candidate_segments

        if not chosen:
            chosen.add(rng.choice(video_ids))
            current_segments = sum(len(video_to_files[v]) for v in chosen)

        if len(chosen) == len(video_ids):
            continue

        error = abs(current_segments - target_test_segments)

        if error < best_error:
            best_error = error
            best_test_videos = chosen

    if best_test_videos is None:
        raise RuntimeError("Test videos seçilemedi.")

    return best_test_videos


def write_split_metadata(train_files, test_files):
    rows = []

    for split_name, files in [("train", train_files), ("test", test_files)]:
        for f in sorted(files):
            rows.append({
                "filename": f.name,
                "relative_path": f"data/processed/{split_name}_set/{LABEL}/{f.name}",
                "video_id": extract_video_id(f.name),
                "label": LABEL,
                "split": split_name,
            })

    SPLIT_METADATA_CSV.parent.mkdir(parents=True, exist_ok=True)

    with SPLIT_METADATA_CSV.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["filename", "relative_path", "video_id", "label", "split"]
        )
        writer.writeheader()
        writer.writerows(rows)


def write_video_summary(video_to_files, train_video_ids, test_video_ids):
    rows = []

    for vid in sorted(video_to_files):
        rows.append({
            "video_id": vid,
            "split": "test" if vid in test_video_ids else "train",
            "segment_count": len(video_to_files[vid]),
        })

    VIDEO_SPLIT_SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)

    with VIDEO_SPLIT_SUMMARY_CSV.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["video_id", "split", "segment_count"]
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    print(f"[INFO] Input dir: {INPUT_DIR}")

    files = sorted(INPUT_DIR.glob("*.wav"))

    if not files:
        print("[ERROR] Clean segment bulunamadı.")
        return

    video_to_files = defaultdict(list)

    for f in files:
        video_id = extract_video_id(f.name)
        video_to_files[video_id].append(f)

    total_segments = len(files)
    total_videos = len(video_to_files)

    print(f"[INFO] Total segments: {total_segments}")
    print(f"[INFO] Total videos: {total_videos}")

    if total_videos < 2:
        print("[ERROR] Train/test split için en az 2 farklı video lazım.")
        return

    test_video_ids = choose_test_videos(video_to_files)
    train_video_ids = set(video_to_files.keys()) - test_video_ids

    train_files = [f for vid in train_video_ids for f in video_to_files[vid]]
    test_files = [f for vid in test_video_ids for f in video_to_files[vid]]

    overlap = train_video_ids & test_video_ids
    if overlap:
        raise RuntimeError(f"DATA LEAKAGE VAR: {overlap}")

    reset_directory(TRAIN_DIR)
    reset_directory(TEST_DIR)

    for f in sorted(train_files):
        shutil.copy2(f, TRAIN_DIR / f.name)

    for f in sorted(test_files):
        shutil.copy2(f, TEST_DIR / f.name)

    write_split_metadata(train_files, test_files)
    write_video_summary(video_to_files, train_video_ids, test_video_ids)

    train_count = len(train_files)
    test_count = len(test_files)

    print("\n[OK] Split tamamlandı.")
    print(f"[INFO] Train videos: {len(train_video_ids)}")
    print(f"[INFO] Test videos: {len(test_video_ids)}")
    print(f"[INFO] Train segments: {train_count}")
    print(f"[INFO] Test segments: {test_count}")
    print(f"[INFO] Train ratio: {train_count / total_segments:.3f}")
    print(f"[INFO] Test ratio: {test_count / total_segments:.3f}")

    print("\n[INFO] Test videos:")
    for vid in sorted(test_video_ids):
        print(f" - {vid}: {len(video_to_files[vid])} segment")

    print(f"\n[OK] Metadata saved: {SPLIT_METADATA_CSV}")
    print(f"[OK] Video summary saved: {VIDEO_SPLIT_SUMMARY_CSV}")


if __name__ == "__main__":
    main()
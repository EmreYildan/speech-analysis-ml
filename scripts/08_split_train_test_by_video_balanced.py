"""

Final clean segmentleri video bazlı train/test'e ayırır.
Önemli fark:
- Aynı video hem train hem test'e girmez.
- Test setini sadece video sayısına göre değil, segment sayısına göre de dengeli seçmeye çalışır.
- Split metadata ve video summary CSV üretir.

Örnek:
python scripts/08_split_train_test_by_video_balanced.py
"""

from __future__ import annotations

import csv
import random
import shutil
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

#bunu kendi hastalık adıyla değiştirin.
LABEL = "normal_speech"

# Clean pool klasörü: audit, manual review ve duplicate temizliği sonrası kalan dosyalar burada olmalı.
INPUT_DIR = PROJECT_ROOT / "data" / "interim" / "segmented_clean_relaxed" / LABEL

TRAIN_DIR = PROJECT_ROOT / "data" / "processed" / "train_set" / LABEL
TEST_DIR = PROJECT_ROOT / "data" / "processed" / "test_set" / LABEL

SPLIT_METADATA_CSV = PROJECT_ROOT / "data" / "metadata" / f"{LABEL}_split_metadata.csv"
VIDEO_SPLIT_SUMMARY_CSV = PROJECT_ROOT / "data" / "metadata" / f"{LABEL}_video_split_summary.csv"

TEST_RATIO = 0.20
SEED = 42

# Rastgele kombinasyon deneme sayısı.
N_TRIALS = 20000


def extract_video_id(filename: str) -> str:
  
    #Example: 7n3YS7GdQ0k_seg_001.wav -> 7n3YS7GdQ0k
   
    return filename.split("_seg_")[0]


def clear_directory(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for f in folder.glob("*.wav"):
        f.unlink()


def choose_balanced_test_videos(
    video_to_files: dict[str, list[Path]],
    test_ratio: float,
    seed: int,
    n_trials: int,
) -> set[str]:

    #Test videolarını segment sayısı hedefe yakın olacak şekilde seçer. Video bazlı leakage'ı engeller.
 
    rng = random.Random(seed)

    video_ids = sorted(video_to_files.keys())
    total_segments = sum(len(files) for files in video_to_files.values())
    target_test_segments = total_segments * test_ratio

    desired_test_video_count = max(1, round(len(video_ids) * test_ratio))

    # 39 video için örn. 7, 8, 9 gibi yakın video sayıları denensin.
    candidate_k_values = sorted({
        max(1, desired_test_video_count - 1),
        desired_test_video_count,
        min(len(video_ids) - 1, desired_test_video_count + 1),
    })

    best_test_videos: set[str] | None = None
    best_score: tuple[float, int] | None = None

    for k in candidate_k_values:
        if k <= 0 or k >= len(video_ids):
            continue

        for _ in range(n_trials):
            chosen = set(rng.sample(video_ids, k))
            test_segments = sum(len(video_to_files[v]) for v in chosen)

            # Öncelik: test segment sayısı hedefe yakın olsun.
            # İkincil: test video sayısı beklenene yakın olsun.
            segment_error = abs(test_segments - target_test_segments)
            video_count_error = abs(k - desired_test_video_count)
            score = (segment_error, video_count_error)

            if best_score is None or score < best_score:
                best_score = score
                best_test_videos = chosen

    if best_test_videos is None:
        raise RuntimeError("Balanced test videos could not be selected.")

    return best_test_videos


def write_split_metadata(
    train_files: list[Path],
    test_files: list[Path],
    split_metadata_csv: Path,
    label: str,
) -> None:
    split_metadata_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for split_name, files in [("train", train_files), ("test", test_files)]:
        for f in sorted(files):
            rows.append({
                "filename": f.name,
                "relative_path": f"data/processed/{split_name}_set/{label}/{f.name}",
                "video_id": extract_video_id(f.name),
                "label": label,
                "split": split_name,
            })

    with split_metadata_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["filename", "relative_path", "video_id", "label", "split"],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_video_summary(
    video_to_files: dict[str, list[Path]],
    train_video_ids: set[str],
    test_video_ids: set[str],
    video_summary_csv: Path,
) -> None:
    video_summary_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for video_id in sorted(video_to_files):
        split_name = "test" if video_id in test_video_ids else "train"
        rows.append({
            "video_id": video_id,
            "split": split_name,
            "segment_count": len(video_to_files[video_id]),
        })

    with video_summary_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=["video_id", "split", "segment_count"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    print(f"[INFO] Input dir: {INPUT_DIR}")
    print(f"[INFO] Train dir: {TRAIN_DIR}")
    print(f"[INFO] Test dir: {TEST_DIR}")

    if not INPUT_DIR.exists():
        print("[ERROR] Input directory does not exist.")
        return

    files = sorted(INPUT_DIR.glob("*.wav"))
    print(f"[INFO] Found {len(files)} segment files.")

    if not files:
        print("[WARNING] No segment files found.")
        return

    video_to_files: dict[str, list[Path]] = defaultdict(list)
    for f in files:
        video_id = extract_video_id(f.name)
        video_to_files[video_id].append(f)

    video_ids = set(video_to_files.keys())
    print(f"[INFO] Found {len(video_ids)} unique videos.")

    test_video_ids = choose_balanced_test_videos(
        video_to_files=video_to_files,
        test_ratio=TEST_RATIO,
        seed=SEED,
        n_trials=N_TRIALS,
    )
    train_video_ids = video_ids - test_video_ids

    train_files = [f for vid in train_video_ids for f in video_to_files[vid]]
    test_files = [f for vid in test_video_ids for f in video_to_files[vid]]

    # Leakage kontrolü
    overlap = train_video_ids & test_video_ids
    if overlap:
        raise RuntimeError(f"Leakage detected. Same videos in train and test: {sorted(overlap)}")

    # Her çalıştırmada train/test klasörlerini temizle
    clear_directory(TRAIN_DIR)
    clear_directory(TEST_DIR)

    for f in sorted(train_files):
        shutil.copy2(f, TRAIN_DIR / f.name)

    for f in sorted(test_files):
        shutil.copy2(f, TEST_DIR / f.name)

    write_split_metadata(train_files, test_files, SPLIT_METADATA_CSV, LABEL)
    write_video_summary(video_to_files, train_video_ids, test_video_ids, VIDEO_SPLIT_SUMMARY_CSV)

    total_segments = len(files)
    train_count = len(train_files)
    test_count = len(test_files)

    print(f"[INFO] Train videos: {len(train_video_ids)}")
    print(f"[INFO] Test videos: {len(test_video_ids)}")
    print(f"[OK] Train segments copied: {train_count}")
    print(f"[OK] Test segments copied: {test_count}")
    print(f"[INFO] Test ratio by segments: {test_count / total_segments:.3f}")
    print(f"[OK] Split metadata saved: {SPLIT_METADATA_CSV}")
    print(f"[OK] Video split summary saved: {VIDEO_SPLIT_SUMMARY_CSV}")

    print("\n[INFO] Test video IDs:")
    for vid in sorted(test_video_ids):
        print(f" - {vid} ({len(video_to_files[vid])} segments)")

    print("\n[INFO] Train video IDs:")
    for vid in sorted(train_video_ids):
        print(f" - {vid} ({len(video_to_files[vid])} segments)")


if __name__ == "__main__":
    main()

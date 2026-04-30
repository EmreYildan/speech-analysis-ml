"""
Clean pool metadata ile split metadata'yı birleştirir.

Input:
- data/metadata/<label>_clean_pool_metadata.csv
- data/metadata/<label>_split_metadata.csv

Output:
- data/metadata/<label>_final_dataset_metadata.csv

Örnek:
python scripts/09_merge_final_metadata_with_split.py --label stuttering
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean pool metadata ile split metadata'yı birleştirir."
    )

    parser.add_argument(
        "--label",
        required=True,
        help="Sınıf etiketi. Örn: spasmodic_dysphonia"
    )

    parser.add_argument(
        "--clean-pool-metadata",
        required=False,
        type=Path,
        default=None,
        help="Clean pool metadata CSV. Verilmezse data/metadata/<label>_clean_pool_metadata.csv kullanılır."
    )

    parser.add_argument(
        "--split-metadata",
        required=False,
        type=Path,
        default=None,
        help="Split metadata CSV. Verilmezse data/metadata/<label>_split_metadata.csv kullanılır."
    )

    parser.add_argument(
        "--output",
        required=False,
        type=Path,
        default=None,
        help="Final dataset metadata CSV. Verilmezse data/metadata/<label>_final_dataset_metadata.csv oluşturulur."
    )

    args = parser.parse_args()

    label = args.label

    clean_pool_metadata = (
        args.clean_pool_metadata
        if args.clean_pool_metadata is not None
        else PROJECT_ROOT / "data" / "metadata" / f"{label}_clean_pool_metadata.csv"
    )

    split_metadata = (
        args.split_metadata
        if args.split_metadata is not None
        else PROJECT_ROOT / "data" / "metadata" / f"{label}_split_metadata.csv"
    )

    output_path = (
        args.output
        if args.output is not None
        else PROJECT_ROOT / "data" / "metadata" / f"{label}_final_dataset_metadata.csv"
    )

    if not clean_pool_metadata.exists():
        raise FileNotFoundError(f"Clean pool metadata bulunamadı: {clean_pool_metadata}")

    if not split_metadata.exists():
        raise FileNotFoundError(f"Split metadata bulunamadı: {split_metadata}")

    clean_rows = read_csv(clean_pool_metadata)
    split_rows = read_csv(split_metadata)

    split_by_filename = {row["filename"]: row["split"] for row in split_rows}

    missing = []

    for row in clean_rows:
        filename = row["filename"]
        split = split_by_filename.get(filename, "")
        row["split"] = split

        if not split:
            missing.append(filename)

    fieldnames = list(clean_rows[0].keys()) if clean_rows else []

    if "split" not in fieldnames:
        fieldnames.append("split")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_rows)

    split_counts = Counter(row["split"] for row in clean_rows)

    print(f"[OK] Saved: {output_path}")
    print(f"[INFO] Label: {label}")
    print(f"[INFO] Total rows: {len(clean_rows)}")
    print(f"[INFO] Train rows: {split_counts.get('train', 0)}")
    print(f"[INFO] Test rows: {split_counts.get('test', 0)}")
    print(f"[INFO] Missing split rows: {len(missing)}")

    if missing:
        print("[WARN] Some clean pool metadata rows did not match split metadata.")
        print("[WARN] First missing filenames:")
        for filename in missing[:10]:
            print(f" - {filename}")


if __name__ == "__main__":
    main()
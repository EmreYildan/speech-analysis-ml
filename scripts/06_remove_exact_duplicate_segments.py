"""


Exact duplicate .wav temizliği yapar:
- Dosyaları SHA256 hash ile karşılaştırır.
- Aynı hash'e sahip dosyalardan 1 tanesini clean klasörde bırakır.
- Diğerlerini duplicates_removed klasörüne taşır.
- CSV raporu üretir.
- Varsayılan olarak dry-run çalışır; gerçek taşıma için --move ver.

Örnek:
python scripts/06_remove_exact_duplicate_segments.py ^
  --input data/interim/segmented_clean_relaxed/spasmodic_dysphonia ^
  --duplicates-dir data/interim/duplicates_removed/spasmodic_dysphonia ^
  --report data/metadata/duplicate_report.csv

Gerçekten taşımak için:
python scripts/06_remove_exact_duplicate_segments.py ^
  --input data/interim/segmented_clean_relaxed/stuttering ^
  --duplicates-dir data/interim/duplicates_removed/stuttering ^
  --report data/metadata/duplicate_report.csv ^
  --move

python scripts/06_remove_exact_duplicate_segments.py --input data/interim/segmented_clean_relaxed/stuttering --duplicates-dir data/interim/duplicates_removed/stuttering --report data/metadata/duplicate_report.csv --move

"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from collections import defaultdict
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    #Dosyanın SHA256 hash'ini hesaplar. 
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def unique_destination(dest_dir: Path, filename: str) -> Path:
    
    #Taşıma sırasında aynı isim varsa üzerine yazmaz.
    #file.wav varsa file__dup1.wav, file__dup2.wav diye yeni isim verir.
    
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    i = 1
    while True:
        candidate = dest_dir / f"{stem}__dup{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exact duplicate .wav segmentlerini bulur ve istenirse duplicate klasörüne taşır."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Temiz segmentlerin bulunduğu klasör."
    )
    parser.add_argument(
        "--duplicates-dir",
        required=True,
        type=Path,
        help="Duplicate dosyaların taşınacağı klasör."
    )
    parser.add_argument(
        "--report",
        required=True,
        type=Path,
        help="CSV duplicate rapor yolu."
    )
    parser.add_argument(
        "--pattern",
        default="*.wav",
        help="Dosya paterni. Varsayılan: *.wav"
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Verilirse duplicate dosyaları taşır. Verilmezse sadece rapor üretir."
    )

    args = parser.parse_args()

    input_dir: Path = args.input
    duplicates_dir: Path = args.duplicates_dir
    report_path: Path = args.report

    if not input_dir.exists():
        raise FileNotFoundError(f"Input klasörü bulunamadı: {input_dir}")

    files = sorted(input_dir.glob(args.pattern))

    if not files:
        print(f"[WARN] Hiç dosya bulunamadı: {input_dir / args.pattern}")
        return

    print(f"[INFO] Found files: {len(files)}")
    print("[INFO] Hash hesaplanıyor...")

    by_hash: dict[str, list[Path]] = defaultdict(list)

    for file_path in files:
        file_hash = sha256_file(file_path)
        by_hash[file_hash].append(file_path)

    duplicate_groups = {
        file_hash: paths
        for file_hash, paths in by_hash.items()
        if len(paths) > 1
    }

    rows = []
    files_to_move: list[tuple[Path, Path, str, Path]] = []

    for file_hash, paths in sorted(duplicate_groups.items()):
        paths = sorted(paths)

        # Her duplicate grupta alfabetik olarak ilk dosyayı tutuyoruz.
        keep_path = paths[0]
        duplicate_paths = paths[1:]

        for dup_path in duplicate_paths:
            dest_path = unique_destination(duplicates_dir, dup_path.name)
            rows.append({
                "hash": file_hash,
                "keep_path": str(keep_path),
                "duplicate_path": str(dup_path),
                "destination_path": str(dest_path),
                "action": "moved" if args.move else "dry_run"
            })
            files_to_move.append((dup_path, dest_path, file_hash, keep_path))

    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "hash",
                "keep_path",
                "duplicate_path",
                "destination_path",
                "action",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[INFO] Duplicate groups: {len(duplicate_groups)}")
    print(f"[INFO] Duplicate files to move: {len(files_to_move)}")
    print(f"[OK] Report saved: {report_path}")

    if args.move:
        duplicates_dir.mkdir(parents=True, exist_ok=True)

        for dup_path, dest_path, _, _ in files_to_move:
            # Dosya daha önce taşındıysa atla.
            if not dup_path.exists():
                print(f"[WARN] Already missing, skipped: {dup_path}")
                continue

            shutil.move(str(dup_path), str(dest_path))

        print(f"[OK] Duplicates moved to: {duplicates_dir}")
    else:
        print("[DRY-RUN] Dosyalar taşınmadı.")
        print("[DRY-RUN] Taşımak için aynı komutu --move ile çalıştır.")


if __name__ == "__main__":
    main()

"""
 
Final clean klasöründeki .wav dosyalarından metadata üretir.

Ne üretiyor:
- data/metadata/clean_pool_metadata.csv
- Her satır 1 segmenttir.
- Duplicate ve quarantine temizliğinden sonra klasörde ne kaldıysa onu final kabul eder.

Örnek:
python scripts/07_make_clean_pool_metadata.py 
--input data/interim/segmented_clean_relaxed/spasmodic_dysphonia 
--label spasmodic_dysphonia
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import wave
from pathlib import Path

import numpy as np


SEGMENT_PATTERN = re.compile(r"^(?P<video_id>.+)_seg_(?P<segment_index>\d+)$")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_wav_info(path: Path) -> dict:
 
    #WAV dosyasından temel audio bilgilerini çıkarır.
    #16-bit PCM wav için en sağlıklı çalışır.
  
    with wave.open(str(path), "rb") as wf:
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()
        duration_s = n_frames / sample_rate if sample_rate else 0.0
        raw = wf.readframes(n_frames)

    # Varsayılan değerler
    rms_dbfs = None
    silence_ratio = None
    clipping_ratio = None

    # En yaygın durum: 16-bit PCM
    if sample_width == 2 and raw:
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

        if channels > 1:
            # [L, R, L, R...] şeklindeki veriyi kanal ortalamasına indir
            audio = audio.reshape(-1, channels).mean(axis=1)

        audio_norm = audio / 32768.0

        rms = float(np.sqrt(np.mean(audio_norm ** 2))) if audio_norm.size else 0.0
        rms_dbfs = 20 * math.log10(rms + 1e-12)

        # 05 scriptindeki mantığa yakın: -45 dBFS altını sessizlik gibi say
        silence_threshold = 10 ** (-45 / 20)
        silence_ratio = float(np.mean(np.abs(audio_norm) < silence_threshold)) if audio_norm.size else 1.0

        # Clipping: sinyalin maksimuma çok yakın olduğu oran
        clipping_ratio = float(np.mean(np.abs(audio_norm) >= 0.99)) if audio_norm.size else 0.0

    return {
        "sample_rate": sample_rate,
        "channels": channels,
        "sample_width_bytes": sample_width,
        "n_frames": n_frames,
        "duration_s": round(duration_s, 4),
        "rms_dbfs": round(rms_dbfs, 2) if rms_dbfs is not None else "",
        "silence_ratio": round(silence_ratio, 4) if silence_ratio is not None else "",
        "clipping_ratio": round(clipping_ratio, 6) if clipping_ratio is not None else "",
    }


def parse_video_and_segment(filename_stem: str) -> tuple[str, str]:
    match = SEGMENT_PATTERN.match(filename_stem)
    if not match:
        return filename_stem, ""
    return match.group("video_id"), match.group("segment_index")


def main() -> None:
    parser = argparse.ArgumentParser(description="clean pool metadata CSV üretir.")
    parser.add_argument("--input", required=True, type=Path, help="Final clean .wav klasörü.")
    parser.add_argument("--output", required=False, type=Path, default=None, help="Çıkacak metadata CSV dosyası.")
    parser.add_argument("--label", default="spasmodic_dysphonia", help="Sınıf etiketi.")
    parser.add_argument("--pattern", default="*.wav", help="Dosya paterni. Varsayılan: *.wav")
    args = parser.parse_args()

    input_dir: Path = args.input
    if args.output is None:
        output_path = Path("data") / "metadata" / f"{args.label}_clean_pool_metadata.csv"
    else:
        output_path = args.output

    if not input_dir.exists():
        raise FileNotFoundError(f"Input klasörü bulunamadı: {input_dir}")

    wav_files = sorted(input_dir.glob(args.pattern))

    rows = []

    for path in wav_files:
        video_id, segment_index = parse_video_and_segment(path.stem)
        audio_info = read_wav_info(path)
        file_hash = sha256_file(path)

        rows.append({
            "filename": path.name,
            "relative_path": str(path).replace("\\", "/"),
            "video_id": video_id,
            "segment_index": segment_index,
            "label": args.label,
            "clean_status": "clean_pool",
            "sha256": file_hash,
            **audio_info,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "filename",
        "relative_path",
        "video_id",
        "segment_index",
        "label",
        "clean_status",
        "sha256",
        "sample_rate",
        "channels",
        "sample_width_bytes",
        "n_frames",
        "duration_s",
        "rms_dbfs",
        "silence_ratio",
        "clipping_ratio",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    unique_videos = sorted({row["video_id"] for row in rows})

    print(f"[OK] Metadata saved: {output_path}")
    print(f"[INFO] Clean pool segments: {len(rows)}")
    print(f"[INFO] Unique videos: {len(unique_videos)}")
    print(f"[INFO] Label: {args.label}")


if __name__ == "__main__":
    main()

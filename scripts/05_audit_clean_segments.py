"""

python scripts/05_audit_clean_segments.py --input data/interim/segmented/stuttering --report data/metadata/stuttering_segment_quality_report_relaxed.csv --copy --clean-dir data/interim/segmented_clean_relaxed/stuttering --quarantine-dir data/interim/quarantine_relaxed/stuttering

"""





from pathlib import Path
import argparse
import csv
import math
import shutil

import numpy as np
import soundfile as sf


def extract_video_id(filename: str) -> str:
    return filename.split("_seg_")[0]


def rms_dbfs(x: np.ndarray) -> float:
    if x.size == 0:
        return -float("inf")
    if x.ndim > 1:
        x = np.mean(x, axis=1)
    rms = float(np.sqrt(np.mean(np.square(x.astype(np.float64))) + 1e-12))
    return 20 * math.log10(max(rms, 1e-12))


def peak_dbfs(x: np.ndarray) -> float:
    if x.size == 0:
        return -float("inf")
    peak = float(np.max(np.abs(x)))
    return 20 * math.log10(max(peak, 1e-12))


def analyze_file(path: Path, expected_sr: int, min_dur: float, max_dur: float,
                 min_dbfs: float, max_silence_ratio: float, max_clipping_ratio: float):
    reasons = []
    try:
        data, sr = sf.read(path, always_2d=False)
    except Exception as e:
        return {
            "path": str(path), "filename": path.name, "video_id": extract_video_id(path.name),
            "ok_read": False, "reason": f"unreadable:{e}", "keep_auto": False
        }

    channels = 1 if data.ndim == 1 else data.shape[1]
    mono = data if data.ndim == 1 else np.mean(data, axis=1)
    duration = len(mono) / sr if sr else 0.0
    dbfs = rms_dbfs(mono)
    peak = peak_dbfs(mono)

    #  ses çok kısık olanlar otomatik seesizlik sayılacak
 
    silence_threshold = 10 ** (-45 / 20)
    silence_ratio = float(np.mean(np.abs(mono) < silence_threshold)) if mono.size else 1.0
    clipping_ratio = float(np.mean(np.abs(mono) >= 0.999)) if mono.size else 0.0

    if sr != expected_sr:
        reasons.append(f"bad_sample_rate:{sr}")
    if channels != 1:
        reasons.append(f"not_mono:{channels}")
    if duration < min_dur:
        reasons.append(f"too_short:{duration:.2f}s")
    if duration > max_dur:
        reasons.append(f"too_long:{duration:.2f}s")
    if dbfs < min_dbfs:
        reasons.append(f"too_quiet:{dbfs:.1f}dBFS")
    if silence_ratio > max_silence_ratio:
        reasons.append(f"mostly_silence:{silence_ratio:.2f}")
    if clipping_ratio > max_clipping_ratio:
        reasons.append(f"clipping:{clipping_ratio:.3f}")

    return {
        "path": str(path),
        "filename": path.name,
        "video_id": extract_video_id(path.name),
        "ok_read": True,
        "sample_rate": sr,
        "channels": channels,
        "duration_s": round(duration, 4),
        "rms_dbfs": round(dbfs, 4),
        "peak_dbfs": round(peak, 4),
        "silence_ratio": round(silence_ratio, 4),
        "clipping_ratio": round(clipping_ratio, 6),
        "keep_auto": len(reasons) == 0,
        "reason": ";".join(reasons) if reasons else "ok",
    }


def main():
    parser = argparse.ArgumentParser(description="Audit and optionally copy clean speech segments.")
    parser.add_argument("--input", required=True, help="Folder containing .wav segment files")
    parser.add_argument("--report", default="data/metadata/segment_quality_report.csv")
    parser.add_argument("--clean-dir", default=None, help="If set with --copy, kept files are copied here")
    parser.add_argument("--quarantine-dir", default=None, help="If set with --copy, flagged files are copied here")
    parser.add_argument("--copy", action="store_true", help="Copy files into clean/quarantine folders")
    parser.add_argument("--expected-sr", type=int, default=16000)
    parser.add_argument("--min-dur", type=float, default=1.5)
    parser.add_argument("--max-dur", type=float, default=3.2)
    parser.add_argument("--min-dbfs", type=float, default=-45.0)
    parser.add_argument("--max-silence-ratio", type=float, default=0.80)
    parser.add_argument("--max-clipping-ratio", type=float, default=0.01)
    args = parser.parse_args()

    input_dir = Path(args.input)
    report_path = Path(args.report)
    files = sorted(input_dir.glob("*.wav"))
    if not files:
        raise SystemExit(f"No .wav files found in {input_dir}")

    rows = [analyze_file(
        f, args.expected_sr, args.min_dur, args.max_dur,
        args.min_dbfs, args.max_silence_ratio, args.max_clipping_ratio
    ) for f in files]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "path", "filename", "video_id", "ok_read", "sample_rate", "channels", "duration_s",
        "rms_dbfs", "peak_dbfs", "silence_ratio", "clipping_ratio", "keep_auto", "reason"
    ]
    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    keep_count = sum(bool(r.get("keep_auto")) for r in rows)
    flag_count = len(rows) - keep_count
    print(f"[OK] Report saved: {report_path}")
    print(f"[INFO] Total: {len(rows)} | keep_auto: {keep_count} | flagged: {flag_count}")

    if args.copy:
        if not args.clean_dir or not args.quarantine_dir:
            raise SystemExit("When using --copy, provide both --clean-dir and --quarantine-dir")
        clean_dir = Path(args.clean_dir)
        quarantine_dir = Path(args.quarantine_dir)
        clean_dir.mkdir(parents=True, exist_ok=True)
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        for r in rows:
            src = Path(r["path"])
            dst = clean_dir / src.name if r.get("keep_auto") else quarantine_dir / src.name
            shutil.copy2(src, dst)
        print(f"[OK] Clean files copied to: {clean_dir}")
        print(f"[OK] Flagged files copied to: {quarantine_dir}")


if __name__ == "__main__":
    main()

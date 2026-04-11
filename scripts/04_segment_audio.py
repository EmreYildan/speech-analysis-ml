from pathlib import Path
from pydub import AudioSegment

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "data" / "interim" / "trimmed" / "stuttering"
OUTPUT_DIR = PROJECT_ROOT / "data" / "interim" / "segmented" / "stuttering"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEGMENT_DURATION_MS = 3000   # 3 saniye
MIN_SEGMENT_MS = 1500        # 1.5 saniyeden kısa parçaları alma

def segment_audio(input_path: Path):
    try:
        audio = AudioSegment.from_wav(input_path)
        total_length = len(audio)

        count = 0
        for start in range(0, total_length, SEGMENT_DURATION_MS):
            end = start + SEGMENT_DURATION_MS
            segment = audio[start:end]

            if len(segment) < MIN_SEGMENT_MS:
                continue

            out_name = f"{input_path.stem}_seg_{count:03d}.wav"
            out_path = OUTPUT_DIR / out_name

            segment.export(out_path, format="wav")
            count += 1

        print(f"[OK] Segmented: {input_path.name} -> {count} segments")

    except Exception as e:
        print(f"[ERROR] {input_path.name}: {e}")

def main():
    print(f"[INFO] Input dir: {INPUT_DIR}")
    print(f"[INFO] Output dir: {OUTPUT_DIR}")

    if not INPUT_DIR.exists():
        print("[ERROR] Input directory does not exist.")
        return

    files = list(INPUT_DIR.glob("*.wav"))
    print(f"[INFO] Found {len(files)} wav files.")

    if not files:
        print("[WARNING] No .wav files found in input directory.")
        return

    for f in files:
        segment_audio(f)

if __name__ == "__main__":
    main()
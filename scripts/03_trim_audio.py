from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "data" / "interim" / "wav_16k" / "stuttering"
OUTPUT_DIR = PROJECT_ROOT / "data" / "interim" / "trimmed" / "stuttering"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_DURATION_MS = 1000       # 1 saniyeden kısa kalırsa atla
MIN_SILENCE_LEN = 400        # 400 ms üstü sessizlikleri dikkate al
SILENCE_THRESH = -40         # sessizlik eşiği (dBFS)
KEEP_PADDING_MS = 150        # konuşmanın başı/sonu biraz kalsın

def trim_audio(input_path: Path, output_path: Path):
    try:
        audio = AudioSegment.from_wav(input_path)

        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=MIN_SILENCE_LEN,
            silence_thresh=SILENCE_THRESH
        )

        if not nonsilent_ranges:
            print(f"[SKIP] No speech detected: {input_path.name}")
            return

        start = max(0, nonsilent_ranges[0][0] - KEEP_PADDING_MS)
        end = min(len(audio), nonsilent_ranges[-1][1] + KEEP_PADDING_MS)

        trimmed_audio = audio[start:end]

        if len(trimmed_audio) < MIN_DURATION_MS:
            print(f"[SKIP] Too short after trim: {input_path.name}")
            return

        trimmed_audio.export(output_path, format="wav")
        print(f"[OK] Trimmed: {input_path.name}")

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
        out_path = OUTPUT_DIR / f.name
        trim_audio(f, out_path)

if __name__ == "__main__":
    main()
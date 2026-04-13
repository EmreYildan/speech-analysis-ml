from pathlib import Path
from pydub import AudioSegment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Burda Dosya dizini kendinize göre ayarlanacaktır örnek stuttering yerine kendi hastalığınızın adını yazabilirsiniz

INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "stuttering"
OUTPUT_DIR = PROJECT_ROOT / "data" / "interim" / "wav_16k" / "stuttering"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".mp4", ".opus", ".ogg"}

def convert_file(input_path: Path, output_path: Path):
    try:
        print(f"[INFO] Reading: {input_path.name}")
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(output_path, format="wav")
        print(f"[OK] Converted: {input_path.name} -> {output_path.name}")
    except Exception as e:
        print(f"[ERROR] {input_path.name}: {e}")

def main():
    print(f"[INFO] Input dir: {INPUT_DIR}")
    print(f"[INFO] Output dir: {OUTPUT_DIR}")

    if not INPUT_DIR.exists():
        print("[ERROR] Input directory does not exist.")
        return

    files = [f for f in INPUT_DIR.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

    print(f"[INFO] Found {len(files)} supported files.")

    if not files:
        print("[WARNING] No supported files found.")
        return

    for file_path in files:
        output_path = OUTPUT_DIR / f"{file_path.stem}.wav"
        if output_path.exists():
            print(f"[SKIP] Already converted: {output_path.name}")
            continue
        convert_file(file_path, output_path)

if __name__ == "__main__":
    main()
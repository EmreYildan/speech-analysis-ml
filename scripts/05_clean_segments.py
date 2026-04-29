from pathlib import Path
import shutil
import librosa
import numpy as np

INPUT_DIR = Path("data/interim/segmented/dysarthria")

CLEAN_DIR = Path("data/processed/clean/dysarthria")
REJECT_DIR = Path("data/processed/rejected/dysarthria")

CLEAN_DIR.mkdir(parents=True, exist_ok=True)
REJECT_DIR.mkdir(parents=True, exist_ok=True)

MIN_DURATION = 1.5
MAX_DURATION = 3.5

MIN_RMS = 0.01
MIN_DB = -35
MIN_NON_SILENT_RATIO = 0.25


# ses ölçme fonksiyonu
def calculate_metrics(file_path):
    y, sr = librosa.load(file_path, sr=16000, mono=True)

    # süre
    duration = librosa.get_duration(y=y, sr=sr)

    # RMS ses enerjisi
    rms = np.sqrt(np.mean(y ** 2))

    # dB seviyesi
    db = librosa.amplitude_to_db(np.array([rms]), ref=1.0)[0]

    # sesli kısımları bul
    intervals = librosa.effects.split(y, top_db=30)

    non_silent_samples = sum(end - start for start, end in intervals)
    non_silent_ratio = non_silent_samples / len(y) if len(y) > 0 else 0

    return duration, rms, db, non_silent_ratio


# karar verme fonksiyonu
def check_quality(duration, rms, db, non_silent_ratio):
    reasons = []

    if duration < MIN_DURATION:
        reasons.append("too_short")

    if duration > MAX_DURATION:
        reasons.append("too_long")

    if rms < MIN_RMS:
        reasons.append("low_rms")

    if db < MIN_DB:
        reasons.append("too_quiet")

    if non_silent_ratio < MIN_NON_SILENT_RATIO:
        reasons.append("mostly_silent")

    return reasons


def main():
    wav_files = list(INPUT_DIR.glob("*.wav"))

    print(f"[INFO] Bulunan segment sayısı: {len(wav_files)}")

    clean_count = 0
    reject_count = 0

    for wav_file in wav_files:
        try:
            duration, rms, db, non_silent_ratio = calculate_metrics(wav_file)
            reasons = check_quality(duration, rms, db, non_silent_ratio)

            if len(reasons) == 0:
                shutil.copy2(wav_file, CLEAN_DIR / wav_file.name)
                clean_count += 1
            else:
                new_name = wav_file.stem + "__" + "_".join(reasons) + ".wav"
                shutil.copy2(wav_file, REJECT_DIR / new_name)
                reject_count += 1

        except Exception as e:
            print(f"[ERROR] {wav_file.name}: {e}")
            shutil.copy2(wav_file, REJECT_DIR / (wav_file.stem + "__error.wav"))
            reject_count += 1

    print("\n[TEMİZLİK BİTTİ]")
    print(f"Temiz kalan: {clean_count}")
    print(f"Reddedilen: {reject_count}")


if __name__ == "__main__":
    main()
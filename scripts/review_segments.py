from pathlib import Path
import shutil
import subprocess

INPUT_DIR = Path("data/interim/segmented_clean_relaxed/stuttering")
BAD_DIR = Path("data/interim/manual_bad/stuttering")

# 🔥 BURAYA KALDIĞIN DOSYA ADINI YAZ
START_FILE = "k8T4dkAcP5g_seg_000.wav"

BAD_DIR.mkdir(parents=True, exist_ok=True)

files = [f for f in sorted(INPUT_DIR.glob("*.wav")) if f.exists()]

print(f"Toplam segment: {len(files)}")
print(f"Başlangıç dosyası: {START_FILE}")
print("k = tut | b = kötüye taşı | s = geç | q = çık")

start_found = False

for i, wav in enumerate(files, start=1):

    if not start_found:
        if wav.name == START_FILE:
            start_found = True
        else:
            continue

    print(f"\n[{i}/{len(files)}] {wav.name}")

    subprocess.Popen(["cmd", "/c", "start", "", str(wav)])

    choice = input("Seçim: ").strip().lower()

    if choice == "b":
        dst = BAD_DIR / wav.name
        shutil.move(str(wav), str(dst))
        print(f"[BAD] Taşındı: {dst}")

    elif choice == "k":
        print("[KEEP] Kaldı.")

    elif choice == "s":
        print("[SKIP] Geçildi.")

    elif choice == "q":
        print("Çıkılıyor.")
        break

    else:
        print("[KEEP] Geçersiz seçim, dosya tutuldu.")
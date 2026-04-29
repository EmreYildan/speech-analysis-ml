from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/processed/final/dysarthria")
OUTPUT_CSV = Path("data/processed/dataset.csv")

rows = []

for wav_file in DATA_DIR.glob("*.wav"):
    rows.append({
        "filepath": str(wav_file),
        "label": "dysarthria"
    })

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"CSV oluşturuldu: {OUTPUT_CSV}")
print(f"Toplam veri: {len(df)}")
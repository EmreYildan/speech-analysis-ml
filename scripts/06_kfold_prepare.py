from pathlib import Path
from sklearn.model_selection import StratifiedKFold
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_DIR = PROJECT_ROOT / "data" / "processed" / "train_set"

N_SPLITS = 5
SEED = 42

def main():
    data = []

    # klasörleri gez (şu an sadece stuttering var)
    for class_dir in TRAIN_DIR.iterdir():
        if not class_dir.is_dir():
            continue

        label = class_dir.name

        for file in class_dir.glob("*.wav"):
            data.append({
                "path": str(file),
                "label": label
            })

    df = pd.DataFrame(data)

    print(f"[INFO] Total samples: {len(df)}")
    print(df["label"].value_counts())

    # label encode (şu an tek sınıf var ama ileride lazım)
    df["label_id"] = df["label"].astype("category").cat.codes

    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

    df["fold"] = -1

    for fold, (_, val_idx) in enumerate(skf.split(df, df["label_id"])):
        df.loc[val_idx, "fold"] = fold

    print("\n[INFO] Fold distribution:")
    print(df.groupby(["fold", "label"]).size())

    # kaydet
    output_path = PROJECT_ROOT / "data" / "metadata" / "kfold_split.csv"
    df.to_csv(output_path, index=False)

    print(f"\n[OK] Saved: {output_path}")

if __name__ == "__main__":
    main()
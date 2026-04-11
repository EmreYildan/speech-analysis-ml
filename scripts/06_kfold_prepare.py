from pathlib import Path
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_DIR = PROJECT_ROOT / "data" / "processed" / "train_set"
OUTPUT_PATH = PROJECT_ROOT / "data" / "metadata" / "kfold_split.csv"

N_SPLITS = 5
SEED = 42


def extract_video_id(filename: str) -> str:
    return filename.split("_seg_")[0]


def main():
    print(f"[INFO] Train dir: {TRAIN_DIR}")
    print(f"[INFO] Output file: {OUTPUT_PATH}")

    if not TRAIN_DIR.exists():
        print("[ERROR] Train directory does not exist.")
        return

    data = []

    for class_dir in TRAIN_DIR.iterdir():
        if not class_dir.is_dir():
            continue

        label = class_dir.name
        files = list(class_dir.glob("*.wav"))
        print(f"[INFO] Found {len(files)} files in class '{label}'")

        for file in files:
            data.append({
                "path": str(file),
                "label": label,
                "video_id": extract_video_id(file.name)
            })

    if not data:
        print("[WARNING] No .wav files found under train_set.")
        return

    df = pd.DataFrame(data)

    print(f"\n[INFO] Total samples: {len(df)}")
    print("[INFO] Label distribution:")
    print(df["label"].value_counts())

    min_class_count = df["label"].value_counts().min()
    if min_class_count < N_SPLITS:
        print(f"[ERROR] At least one class has fewer than {N_SPLITS} samples.")
        return

    unique_group_counts = df.groupby("label")["video_id"].nunique()
    if unique_group_counts.min() < N_SPLITS:
        print(f"[ERROR] At least one class has fewer than {N_SPLITS} unique videos.")
        print("[INFO] Unique video counts per class:")
        print(unique_group_counts)
        return

    df["label_id"] = df["label"].astype("category").cat.codes
    df["fold"] = -1

    sgkf = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=SEED
    )

    for fold, (_, val_idx) in enumerate(
        sgkf.split(df, y=df["label_id"], groups=df["video_id"])
    ):
        df.loc[val_idx, "fold"] = fold

    print("\n[INFO] Fold distribution:")
    print(df.groupby(["fold", "label"]).size())

    print("\n[INFO] Unique videos per fold:")
    print(df.groupby("fold")["video_id"].nunique())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"\n[OK] Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
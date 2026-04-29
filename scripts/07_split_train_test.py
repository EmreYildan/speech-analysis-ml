from pathlib import Path
import pandas as pd
import random

df = pd.read_csv("data/processed/dataset.csv")

df["video_id"] = df["filepath"].apply(lambda x: Path(x).stem.split("_seg_")[0])

video_ids = df["video_id"].unique().tolist()
random.shuffle(video_ids)

train_ids = []
test_ids = []

train_count = 0
total = len(df)
target_train = int(total * 0.8)

for vid in video_ids:
    vid_count = len(df[df["video_id"] == vid])
    
    if train_count + vid_count <= target_train:
        train_ids.append(vid)
        train_count += vid_count
    else:
        test_ids.append(vid)

train_df = df[df["video_id"].isin(train_ids)]
test_df = df[df["video_id"].isin(test_ids)]

train_df.to_csv("data/processed/train.csv", index=False)
test_df.to_csv("data/processed/test.csv", index=False)

print("Train:", len(train_df))
print("Test:", len(test_df))
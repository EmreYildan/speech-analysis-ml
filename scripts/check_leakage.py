import pandas as pd
from pathlib import Path

train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")

train_ids = set(train["filepath"].apply(lambda x: Path(x).stem.split("_seg_")[0]))
test_ids = set(test["filepath"].apply(lambda x: Path(x).stem.split("_seg_")[0]))

common = train_ids.intersection(test_ids)

print("Ortak video sayısı:", len(common))

if len(common) == 0:
    print("Süper! Leakage yok")
else:
    print("Problem var!")
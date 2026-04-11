# 1. python -m venv venv
# 2. pip install yt-dlp librosa soundfile pandas numpy scikit-learn matplotlib tqdm noisereduce pydub

MakineProje/
│
├── data/
│   ├── raw/
│   │   └── stuttering/
│   │
│   ├── interim/
│   │   ├── wav_16k/
│   │   │   └── stuttering/
│   │   ├── trimmed/
│   │   │   └── stuttering/
│   │   └── segmented/
│   │       └── stuttering/
│   │
│   ├── processed/
│   │   ├── train_set/
│   │   │   └── stuttering/
│   │   ├── validation_set/
│   │   │   └── stuttering/
│   │   └── test_set/
│   │       └── stuttering/
│   │
│   └── metadata/
│       ├── video_urls_stuttering.txt
│       ├── raw_metadata.csv
│       ├── stuttering_segments.csv
│       └── split_metadata.csv
│
├── scripts/
│   ├── 01_download_audio.py
│   ├── 02_standardize_audio.py
│   ├── 03_trim_audio.py
│   ├── 04_segment_audio.py
│   ├── 05_create_metadata.py
│   └── 06_split_dataset.py
│
├── notebooks/
├── reports/
├── venv/
├── README.md
└── requirements.txt


# B C D E SINIFLARI kİM ARASINDA DAĞITILCAKSA ONA GÖRE ANLAŞIP KLASÖR YAPISI BU ŞEKİLDE OLACAKTIR 
MakineProje/
│
├── data/
│   ├── raw/
│   │   ├── stuttering/
│   │   ├── member_b/
│   │   ├── member_c/
│   │   ├── member_d/
│   │   └── member_e/
│   │
│   ├── interim/
│   │   ├── wav_16k/
│   │   │   ├── stuttering/
│   │   │   ├── member_b/
│   │   │   ├── member_c/
│   │   │   ├── member_d/
│   │   │   └── member_e/
│   │   │
│   │   ├── trimmed/
│   │   │   ├── stuttering/
│   │   │   ├── member_b/
│   │   │   ├── member_c/
│   │   │   ├── member_d/
│   │   │   └── member_e/
│   │   │
│   │   └── segmented/
│   │       ├── stuttering/
│   │       ├── member_b/
│   │       ├── member_c/
│   │       ├── member_d/
│   │       └── member_e/
│   │
│   ├── processed/
│   │   ├── train_set/
│   │   │   ├── stuttering/
│   │   │   ├── member_b/
│   │   │   ├── member_c/
│   │   │   ├── member_d/
│   │   │   └── member_e/
│   │   │
│   │   │   
│   │   └── test_set/
│   │       ├── stuttering/
│   │       ├── member_b/
│   │       ├── member_c/
│   │       ├── member_d/
│   │       └── member_e/
│   │
│   └── metadata/
│       ├── stuttering_urls.txt
│       ├── member_b_urls.txt
│       ├── member_c_urls.txt
│       ├── member_d_urls.txt
│       ├── member_e_urls.txt
│       ├── raw_metadata.csv
│       ├── segments_metadata.csv
│       └── split_metadata.csv
│
├── scripts/
├── notebooks/
├── reports/
├── README.md
└── requirements.txt
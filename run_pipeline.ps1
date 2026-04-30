# .\run_pipeline.ps1

$ErrorActionPreference = "Stop"

function Run-Step {
    param(
        [string]$Name,
        [string]$Command,
        [string]$CheckPath
    )

    Write-Host ""
    Write-Host $Name

    if ($CheckPath -and (Test-Path $CheckPath)) {
        Write-Host "[SKIP] Already exists: $CheckPath"
        return
    }

    Invoke-Expression $Command

    if ($LASTEXITCODE -ne 0) {
        Write-Error "[FAILED] $Name"
        exit $LASTEXITCODE
    }
}

Run-Step "STEP 01: download" "python scripts/01_download_data.py" "data/raw/stuttering"

Run-Step "STEP 02: convert" "python scripts/02_convert_to_wav16k.py" "data/interim/wav_16k/stuttering"

Run-Step "STEP 03: trim" "python scripts/03_trim_audio.py" "data/interim/trimmed/stuttering"

Run-Step "STEP 04: segment" "python scripts/04_segment_audio.py" "data/interim/segmented/stuttering"

Run-Step "STEP 05: clean" "python scripts/05_audit_clean_segments.py --input data/interim/segmented/stuttering --report data/metadata/stuttering_segment_quality_report_relaxed.csv --copy --clean-dir data/interim/segmented_clean_relaxed/stuttering --quarantine-dir data/interim/quarantine_relaxed/stuttering" ""

Run-Step "STEP 06: remove duplicates" "python scripts/06_remove_exact_duplicate_segments.py --input data/interim/segmented_clean_relaxed/stuttering --duplicates-dir data/interim/duplicates_removed/stuttering --report data/metadata/duplicate_report.csv --move" ""

Run-Step "STEP 07: metadata" "python scripts/07_make_clean_pool_metadata.py --input data/interim/segmented_clean_relaxed/stuttering --label stuttering --output data/metadata/stuttering_clean_pool_metadata.csv" ""

Run-Step "STEP 08: split train/test by video" "python scripts/08_split_train_test_by_video_balanced.py" ""

Run-Step "STEP 09: merge final metadata with split" "python scripts/09_merge_final_metadata_with_split.py --label stuttering" ""

Run-Step "STEP 10: kfold prepare" "python scripts/10_kfold_prepare.py" ""

Write-Host ""
Write-Host "PIPELINE COMPLETED"
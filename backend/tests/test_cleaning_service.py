from pathlib import Path

import pandas as pd

from app.services.cleaning_service import run_optional_cleaning


def test_run_optional_cleaning_generates_cleaned_artifact(tmp_path: Path) -> None:
    run_dir = tmp_path / "run1"
    extracted = run_dir / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)

    csv_path = extracted / "train.csv"
    csv_path.write_text(
        "age,mixed,city\n"
        "30,1,LA\n"
        "30,1,LA\n"
        "31,,NY\n"
        "32,2,SF\n",
        encoding="utf-8",
    )

    ingestion_output = {
        "selected_file_path": str(csv_path),
        "dataset_metadata": {"delimiter": ","},
    }

    result = run_optional_cleaning(ingestion_output)

    assert result["status"] == "completed"
    assert result["rows_before"] == 4
    assert result["rows_after"] == 3
    assert result["rows_removed"] == 1
    assert result["duplicate_rows_removed"] >= 1
    assert "mixed" in result["imputed_columns"]

    cleaned_path = Path(result["cleaned_file_path"])
    assert cleaned_path.exists()

    cleaned_df = pd.read_csv(cleaned_path)
    assert cleaned_df["mixed"].isna().sum() == 0


def test_run_optional_cleaning_skips_when_path_missing() -> None:
    result = run_optional_cleaning({})

    assert result["status"] == "skipped"
    assert "selected_file_path" in result["reason"]

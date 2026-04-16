import asyncio
from pathlib import Path

from app.services.profiling_service import run_profiling


def test_run_profiling_reads_real_csv_metadata(tmp_path: Path) -> None:
    csv_path = tmp_path / "profile.csv"
    csv_path.write_text("age,income,city\n34,70000,LA\n29,,NY\n", encoding="utf-8")

    ingestion_output = {
        "selected_file": "profile.csv",
        "selected_file_path": str(csv_path),
        "dataset_metadata": {"delimiter": ","},
    }

    profile = asyncio.run(run_profiling(ingestion_output))

    assert profile["rows"] == 2
    assert profile["columns"] == 3
    assert profile["column_names"] == ["age", "income", "city"]
    assert "age" in profile["column_types"]["numerical"]
    assert "city" in profile["column_types"]["categorical"]

    missing_by_column = {item["column"]: item for item in profile["missing_values"]["by_column"]}
    assert missing_by_column["income"]["missing_count"] == 1


def test_run_profiling_falls_back_to_simulated_without_selected_path() -> None:
    ingestion_output = {
        "selected_file": "train.csv",
        "dataset_metadata": {
            "row_count": 10,
            "column_count": 2,
            "column_names": ["f1", "f2"],
        },
    }

    profile = asyncio.run(run_profiling(ingestion_output))

    assert profile["rows"] == 10
    assert profile["columns"] == 2
    assert profile["column_names"] == ["f1", "f2"]
    assert profile["note"].startswith("Simulated profiling")

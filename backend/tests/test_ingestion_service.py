import asyncio
from pathlib import Path

from app.schemas.dataset import KaggleDatasetInput
from app.services.ingestion_service import _collect_dataset_metadata, run_ingestion
from app.utils.file_utils import select_primary_csv


def test_collect_dataset_metadata_reads_row_column_counts(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")

    metadata = _collect_dataset_metadata(csv_path)

    assert metadata["row_count"] == 2
    assert metadata["column_count"] == 3
    assert metadata["column_names"] == ["a", "b", "c"]
    assert metadata["delimiter"] == ","


def test_select_primary_csv_prefers_train_csv(tmp_path: Path) -> None:
    train_path = tmp_path / "train.csv"
    train_path.write_text("x\n1\n", encoding="utf-8")

    other_path = tmp_path / "data.csv"
    other_path.write_text("x\n1\n2\n3\n", encoding="utf-8")

    selected = select_primary_csv([other_path, train_path])

    assert selected == train_path


def test_run_ingestion_simulated_mode_contains_metadata() -> None:
    payload = KaggleDatasetInput(competition="titanic")
    result = asyncio.run(run_ingestion(payload))

    assert result["source"] == "kaggle"
    assert result["competition"] == "titanic"
    assert result["dataset_metadata"]["column_count"] > 0

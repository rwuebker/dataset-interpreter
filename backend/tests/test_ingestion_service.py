import asyncio
from dataclasses import replace
from pathlib import Path
from zipfile import ZipFile

from app.schemas.dataset import KaggleDatasetInput
from app.services import ingestion_service
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


def test_real_ingestion_downloads_once_and_reuses_cached_raw_data(tmp_path: Path, monkeypatch) -> None:
    settings_override = replace(
        ingestion_service.settings,
        dataset_storage_root=tmp_path,
        kaggle_username="demo-user",
        kaggle_key="demo-key",
    )
    monkeypatch.setattr(ingestion_service, "settings", settings_override)
    monkeypatch.setattr(ingestion_service, "_COMPETITION_CACHE_LOCKS", {})

    class FakeKaggleClient:
        download_calls = 0

        def __init__(self, username: str, key: str) -> None:
            self.username = username
            self.key = key

        def download_competition_zip(self, competition: str, destination: Path) -> Path:
            FakeKaggleClient.download_calls += 1
            zip_path = destination / f"{competition}.zip"
            with ZipFile(zip_path, "w") as archive:
                archive.writestr("train.csv", "a,b\n1,2\n3,4\n")
                archive.writestr("test.csv", "a,b\n5,6\n")
            return zip_path

    monkeypatch.setattr(ingestion_service, "KaggleClient", FakeKaggleClient)

    payload = KaggleDatasetInput(competition="titanic")
    first = ingestion_service._run_real_ingestion(payload)
    second = ingestion_service._run_real_ingestion(payload)

    assert FakeKaggleClient.download_calls == 1
    assert first["download_performed"] is True
    assert second["download_performed"] is False
    assert second["cache_hit"] is True
    assert "reused cached raw data" in second["note"].lower()
    assert first["selected_file_path"] == second["selected_file_path"]
    assert first["analysis_output_dir"] != second["analysis_output_dir"]

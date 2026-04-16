import asyncio
from pathlib import Path

from app.services.issue_detection_service import run_issue_detection
from app.services.profiling_service import run_profiling


def test_issue_detection_flags_duplicates_outliers_and_type_inconsistencies(tmp_path: Path) -> None:
    csv_path = tmp_path / "issues.csv"
    csv_path.write_text(
        "age,mixed,target\n"
        "30,1,0\n"
        "30,1,0\n"
        "31,abc,1\n"
        "500,2,1\n",
        encoding="utf-8",
    )

    ingestion_output = {
        "selected_file": "issues.csv",
        "selected_file_path": str(csv_path),
        "dataset_metadata": {"delimiter": ","},
    }

    profile = asyncio.run(run_profiling(ingestion_output))
    issues = asyncio.run(run_issue_detection(profile, ingestion_output))

    assert issues["summary"]["duplicate_rows"] >= 1
    assert issues["outliers"] in {"low", "moderate", "high"}
    assert issues["type_inconsistencies"] == "detected"
    assert "mixed" in issues["summary"]["inconsistent_columns"]
    assert any(issue["issue_type"] == "duplicates" for issue in issues["issues"])


def test_issue_detection_without_selected_path_uses_profile_only() -> None:
    profile_output = {
        "rows": 100,
        "missing_values": {
            "missing_percent": 12.5,
        },
    }

    issues = asyncio.run(run_issue_detection(profile_output, ingestion_output=None))

    assert issues["missing_data"] == "high"
    assert issues["duplicates"] == "none"
    assert issues["outliers"] == "none"

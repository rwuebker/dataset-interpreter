from pathlib import Path
from zipfile import ZipFile


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_zip_archive(zip_path: Path, destination: Path) -> Path:
    ensure_dir(destination)
    with ZipFile(zip_path, "r") as archive:
        archive.extractall(destination)
    return destination


def find_csv_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.csv") if path.is_file()]


def select_primary_csv(csv_files: list[Path]) -> Path | None:
    if not csv_files:
        return None

    for path in csv_files:
        if path.name.lower() == "train.csv":
            return path

    return max(csv_files, key=lambda candidate: candidate.stat().st_size)

import os
from pathlib import Path

from requests import HTTPError

from app.utils.file_utils import ensure_dir


class KaggleClient:
    def __init__(self, username: str | None = None, key: str | None = None, api_token: str | None = None) -> None:
        self._username = username
        self._key = key
        self._api_token = api_token

    def download_competition_zip(self, competition: str, destination: Path) -> Path:
        ensure_dir(destination)

        # Kaggle API supports access token mode and legacy username/key mode.
        if self._api_token:
            os.environ["KAGGLE_API_TOKEN"] = self._api_token
            os.environ.pop("KAGGLE_USERNAME", None)
            os.environ.pop("KAGGLE_KEY", None)
        else:
            if not self._username or not self._key:
                raise RuntimeError(
                    "Kaggle credentials missing: provide KAGGLE_API_TOKEN or KAGGLE_USERNAME/KAGGLE_KEY."
                )
            os.environ["KAGGLE_USERNAME"] = self._username
            os.environ["KAGGLE_KEY"] = self._key
            os.environ.pop("KAGGLE_API_TOKEN", None)

        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()
        try:
            api.competition_download_files(competition, path=str(destination), quiet=True)
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 401:
                raise RuntimeError(
                    "Kaggle rejected competition download (401 Unauthorized). "
                    "Check KAGGLE_USERNAME/KAGGLE_KEY, verify token has download permissions, "
                    f"and accept competition rules at https://www.kaggle.com/competitions/{competition}/overview."
                ) from exc
            raise RuntimeError(
                f"Kaggle competition download failed for '{competition}' with HTTP status {status_code}."
            ) from exc

        expected_zip = destination / f"{competition}.zip"
        if expected_zip.exists():
            return expected_zip

        downloaded_zips = sorted(destination.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
        if downloaded_zips:
            return downloaded_zips[0]

        raise RuntimeError(f"Kaggle zip download did not produce an archive for '{competition}'.")

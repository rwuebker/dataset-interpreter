from enum import Enum

from pydantic import BaseModel


class DatasetSourceType(str, Enum):
    KAGGLE = "kaggle"
    CSV_UPLOAD = "csv_upload"


class KaggleDatasetInput(BaseModel):
    competition: str


class CSVUploadPlaceholderInput(BaseModel):
    filename: str | None = None


class CreateJobRequest(BaseModel):
    source_type: DatasetSourceType
    kaggle: KaggleDatasetInput | None = None
    csv_upload: CSVUploadPlaceholderInput | None = None

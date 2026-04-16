from app.schemas.dataset import KaggleDatasetInput


async def run_ingestion(dataset: KaggleDatasetInput) -> dict:
    return {
        "source": "kaggle",
        "competition": dataset.competition,
        "selected_file": "train.csv",
        "note": "Simulated ingestion stage (real Kaggle download not implemented yet).",
    }

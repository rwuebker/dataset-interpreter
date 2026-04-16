async def run_profiling(ingestion_output: dict) -> dict:
    return {
        "rows": 1000,
        "columns": 12,
        "column_types": {
            "numerical": 8,
            "categorical": 4,
        },
        "note": "Simulated profiling stage (real stats not implemented yet).",
        "ingestion_ref": ingestion_output.get("selected_file"),
    }

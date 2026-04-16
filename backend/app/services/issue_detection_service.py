async def run_issue_detection(profile_output: dict) -> dict:
    return {
        "missing_data": "moderate",
        "duplicates": "low",
        "outliers": "low",
        "type_inconsistencies": "none_detected",
        "note": "Simulated issue detection stage (real checks not implemented yet).",
        "profile_rows_ref": profile_output.get("rows"),
    }

from fastapi import Body
import csv
import json
from pathlib import Path

COMPLETED_CSV = Path(__file__).resolve().parent / "completed_requests.csv"


@app.post("/completeRequest")
async def complete_request(agent_result: dict = Body(...)):

    file_exists = COMPLETED_CSV.exists()

    with open(
        COMPLETED_CSV,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "request_id",
                "agent_response"
            ])

        writer.writerow([
            agent_result.get("request_id", ""),
            json.dumps(agent_result, ensure_ascii=False)
        ])

    return {
        "success": True,
        "message": "Request saved successfully"
    }

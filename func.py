from pathlib import Path
import csv
from fastapi import FastAPI

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
INCOMING_CSV = BASE_DIR / "incoming_requests.csv"


@app.get("/api/registrar/requests")
async def get_incoming_requests():

    requests = []

    with open(INCOMING_CSV, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            requests.append(row)

    return {
        "success": True,
        "requests": requests
    }

@app.post("/completeRequest")
async def complete_request(agent_result: dict = Body(...)):

    request_id = agent_result.get("request_id")

    # -------------------------------------------------
    # 1. SAVE AGENT RESPONSE TO COMPLETED CSV
    # -------------------------------------------------

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
            request_id,
            json.dumps(agent_result, ensure_ascii=False)
        ])


    # -------------------------------------------------
    # 2. REMOVE REQUEST FROM INCOMING CSV
    # -------------------------------------------------

    with open(
        INCOMING_CSV,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        fieldnames = reader.fieldnames

        rows = [
            row for row in reader
            if row.get("request_id") != request_id
        ]


    # Rewrite incoming CSV without the completed request

    with open(
        INCOMING_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)


    return {
        "success": True,
        "message": "Request saved and removed from incoming requests",
        "request_id": request_id
    }

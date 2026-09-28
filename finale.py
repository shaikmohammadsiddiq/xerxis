@app.post("/submitRequest")
async def submit_request(data: dict = Body(...)):

    # Generate request ID
    request_id = "REQ" + datetime.now().strftime("%Y%m%d%H%M%S")

    submitted_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    row = {
        "request_id": request_id,
        "student_id": data.get("student_id", ""),
        "student_name": data.get("student_name", ""),
        "student_status": data.get("student_status", ""),
        "request_type": data.get("request_type", ""),
        "body_text": data.get("body_text", ""),
        "submitted_at": submitted_at,
        "status": "NEW"
    }

    # Check whether CSV already exists
    file_exists = INCOMING_CSV.exists()

    with open(
        INCOMING_CSV,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        fieldnames = [
            "request_id",
            "student_id",
            "student_name",
            "student_status",
            "request_type",
            "body_text",
            "submitted_at",
            "status"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


    return {
        "success": True,
        "message": "Request submitted successfully",
        "request_id": request_id
    }

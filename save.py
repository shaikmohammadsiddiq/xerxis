def save_completed_request(request, result):

    file_exists = COMPLETED_CSV.exists()

    row = {
        "request_id": request["request_id"],
        "student_name": request["student_name"],
        "student_status": request["student_status"],
        "body_text": request["body_text"],
        "classification": result.get("classification", ""),
        "decision": result.get("decision", ""),
        "actions_taken": json.dumps(
            result.get("actions_taken", []),
            ensure_ascii=False
        ),
        "reason": result.get("reason", "")
    }

    fieldnames = [
        "request_id",
        "student_name",
        "student_status",
        "body_text",
        "classification",
        "decision",
        "actions_taken",
        "reason"
    ]

    with open(
        COMPLETED_CSV,
        "a",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

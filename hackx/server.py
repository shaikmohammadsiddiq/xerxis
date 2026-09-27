from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = Path(__file__).resolve().parent

REQUESTS_CSV = BASE / "student_service_requests.csv"
BILLING_CSV = BASE / "student_billing_records.csv"
ACTIONS_JSON = BASE / "actions.json"


mcp = FastMCP("Higher-Education Registrar Agent")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file and return rows as dictionaries."""

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path.name}")

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def save_action(
    action_type: str,
    request_id: str,
    details: dict[str, Any]
) -> dict[str, Any]:

    if ACTIONS_JSON.exists():
        try:
            actions = json.loads(
                ACTIONS_JSON.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            actions = []
    else:
        actions = []

    action = {
        "action_id": (
            f"ACT-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        ),
        "timestamp": now(),
        "action_type": action_type,
        "request_id": request_id,
        "details": details,
    }

    actions.append(action)

    ACTIONS_JSON.write_text(
        json.dumps(
            actions,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8",
    )

    return action


# ============================================================
# TOOL 1
# CHECK RELATED REQUEST HISTORY
# ============================================================

@mcp.tool
def check_related_history(
    student_name: str,
    body_text: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Check whether this student has submitted previous
    requests related to the current request.

    Process:
        1. Filter by student_name
        2. Compare body_text using TF-IDF
        3. Return the most related historical requests

    This tool does NOT call an LLM.
    """

    rows = read_csv(REQUESTS_CSV)

    # Only search this student's previous requests
    student_rows = [
        row
        for row in rows
        if row.get("student_name", "").strip().lower()
        == student_name.strip().lower()
    ]

    if not student_rows:
        return {
            "student_name": student_name,
            "historical_request_count": 0,
            "related_found": False,
            "matches": [],
        }

    texts = [
        row.get("body_text", "")
        for row in student_rows
    ]

    try:

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
        )

        matrix = vectorizer.fit_transform(
            texts + [body_text]
        )

        scores = cosine_similarity(
            matrix[-1],
            matrix[:-1]
        ).flatten()

    except ValueError:

        return {
            "student_name": student_name,
            "historical_request_count": len(student_rows),
            "related_found": False,
            "matches": [],
        }

    ranked = sorted(
        zip(student_rows, scores),
        key=lambda x: float(x[1]),
        reverse=True,
    )

    top_k = max(1, min(int(top_k), 10))

    matches = []

    for row, score in ranked[:top_k]:

        matches.append({
            "request_id": row.get("request_id"),
            "student_name": row.get("student_name"),
            "student_status": row.get("student_status"),
            "status": row.get("status"),
            "submitted_at": row.get("submitted_at"),
            "body_text": row.get("body_text"),
            "similarity": round(float(score), 4),
        })

    return {
        "student_name": student_name,
        "historical_request_count": len(student_rows),
        "related_found": bool(matches),
        "matches": matches,
    }


# ============================================================
# TOOL 2
# GET REQUEST DETAILS
# ============================================================

@mcp.tool
def get_request_details(
    request_id: str,
) -> dict[str, Any]:
    """
    Retrieve a complete historical request using request_id.
    """

    rows = read_csv(REQUESTS_CSV)

    for row in rows:

        if (
            row.get("request_id", "").strip().lower()
            == request_id.strip().lower()
        ):

            return {
                "found": True,
                "request": row,
            }

    return {
        "found": False,
        "request_id": request_id,
    }


# ============================================================
# TOOL 3
# CHECK BILLING DISCREPANCY
# ============================================================

@mcp.tool
def check_billing_discrepancy(
    student_name: str,
    body_text: str,
) -> dict[str, Any]:
    """
    Check the student's verified billing discrepancy.

    The billing CSV contains:

        student_name
        verified_discrepancy

    The tool returns the actual billing evidence.

    The AGENT decides what that evidence means.
    """

    rows = read_csv(BILLING_CSV)

    matches = [
        row
        for row in rows
        if row.get("student_name", "").strip().lower()
        == student_name.strip().lower()
    ]

    if not matches:

        return {
            "found": False,
            "student_name": student_name,
            "message": "No billing record found.",
        }

    records = []

    for row in matches:

        raw_value = row.get(
            "verified_discrepancy",
            ""
        )

        try:
            discrepancy = float(raw_value)
        except ValueError:
            discrepancy = raw_value

        records.append({
            "student_name": row.get("student_name"),
            "verified_discrepancy": discrepancy,
        })

    return {
        "found": True,
        "student_name": student_name,
        "student_statement": body_text,
        "billing_records": records,
    }


# ============================================================
# TOOL 4
# ROUTE REQUEST
# ============================================================

@mcp.tool
def route_request(
    request_id: str,
    department: str,
    priority: str = "normal",
) -> dict[str, Any]:
    """
    Route a request to the appropriate university department.
    """

    priority = priority.lower()

    if priority not in {
        "low",
        "normal",
        "high",
        "urgent",
    }:

        return {
            "success": False,
            "error": (
                "priority must be "
                "low, normal, high, or urgent"
            ),
        }

    action = save_action(
        "route_request",
        request_id,
        {
            "department": department,
            "priority": priority,
        },
    )

    return {
        "success": True,
        "status": "routed",
        "department": department,
        "action_id": action["action_id"],
    }


# ============================================================
# TOOL 5
# ACKNOWLEDGE REQUEST
# ============================================================

@mcp.tool
def acknowledge_request(
    request_id: str,
    message: str,
) -> dict[str, Any]:
    """
    Record an automated acknowledgement.
    """

    action = save_action(
        "acknowledge_request",
        request_id,
        {
            "message": message,
        },
    )

    return {
        "success": True,
        "status": "acknowledged",
        "action_id": action["action_id"],
    }


# ============================================================
# TOOL 6
# CLOSE DUPLICATE
# ============================================================

@mcp.tool
def close_duplicate_request(
    request_id: str,
    related_request_id: str,
    reason: str,
) -> dict[str, Any]:
    """
    Close a request that the agent determined
    to be a duplicate.
    """

    action = save_action(
        "close_duplicate_request",
        request_id,
        {
            "related_request_id": related_request_id,
            "reason": reason,
        },
    )

    return {
        "success": True,
        "status": "closed_as_duplicate",
        "action_id": action["action_id"],
    }


# ============================================================
# TOOL 7
# FLAG FOR HUMAN REVIEW
# ============================================================

@mcp.tool
def flag_for_human_review(
    request_id: str,
    reason: str,
    priority: str = "high",
) -> dict[str, Any]:
    """
    Send a request to the human review queue.
    """

    priority = priority.lower()

    if priority not in {
        "low",
        "normal",
        "high",
        "urgent",
    }:

        return {
            "success": False,
            "error": (
                "priority must be "
                "low, normal, high, or urgent"
            ),
        }

    action = save_action(
        "flag_for_human_review",
        request_id,
        {
            "reason": reason,
            "priority": priority,
        },
    )

    return {
        "success": True,
        "status": "human_review",
        "action_id": action["action_id"],
    }


# ============================================================
# TOOL 8
# ISSUE COURTESY RESOLUTION
# ============================================================

@mcp.tool
def issue_courtesy_resolution(
    request_id: str,
    student_name: str,
    reason: str,
) -> dict[str, Any]:
    """
    Issue the automated courtesy resolution for
    an eligible Tuition & Fee Billing case.
    """

    action = save_action(
        "issue_courtesy_resolution",
        request_id,
        {
            "student_name": student_name,
            "reason": reason,
        },
    )

    return {
        "success": True,
        "status": "courtesy_resolution_issued",
        "action_id": action["action_id"],
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    missing_files = [
        path.name
        for path in (
            REQUESTS_CSV,
            BILLING_CSV,
        )
        if not path.exists()
    ]

    if missing_files:

        print("Missing required CSV files:")

        for filename in missing_files:
            print(" -", filename)

        raise SystemExit(1)

    mcp.run()

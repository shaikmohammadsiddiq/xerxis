from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# CONFIGURATION
# ============================================================

BASE = Path(__file__).resolve().parent

REQUESTS_CSV = BASE / "student_service_requests.csv"
BILLING_CSV = BASE / "student_billing_records.csv"


mcp = FastMCP("Higher-Education Registrar Agent")


# ============================================================
# COMMON FUNCTION
# ============================================================

def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file and return rows as dictionaries."""

    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path.name}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


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

    try:
        rows = read_csv(REQUESTS_CSV)

        # Only search this student's previous requests
        student_rows = [
            row
            for row in rows
            if row.get(
                "student_name",
                ""
            ).strip().lower()
            == student_name.strip().lower()
        ]

        if not student_rows:
            return {
                "success": True,
                "student_name": student_name,
                "historical_request_count": 0,
                "related_found": False,
                "matches": [],
            }

        texts = [
            row.get(
                "body_text",
                ""
            )
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

        except ValueError as e:
            return {
                "success": False,
                "tool": "check_related_history",
                "error": str(e),
            }

        ranked = sorted(
            zip(student_rows, scores),
            key=lambda x: float(x[1]),
            reverse=True,
        )

        top_k = max(
            1,
            min(int(top_k), 10)
        )

        matches = []

        for row, score in ranked[:top_k]:

            matches.append({
                "request_id": row.get(
                    "request_id"
                ),
                "student_name": row.get(
                    "student_name"
                ),
                "student_status": row.get(
                    "student_status"
                ),
                "status": row.get(
                    "status"
                ),
                "submitted_at": row.get(
                    "submitted_at"
                ),
                "body_text": row.get(
                    "body_text"
                ),
                "similarity": round(
                    float(score),
                    4
                ),
            })

        return {
            "success": True,
            "student_name": student_name,
            "historical_request_count": len(
                student_rows
            ),
            "related_found": bool(matches),
            "matches": matches,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "check_related_history",
            "error": str(e),
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

    try:
        rows = read_csv(REQUESTS_CSV)

        for row in rows:

            if (
                row.get(
                    "request_id",
                    ""
                ).strip().lower()
                == request_id.strip().lower()
            ):

                return {
                    "success": True,
                    "found": True,
                    "request": row,
                }

        return {
            "success": True,
            "found": False,
            "request_id": request_id,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "get_request_details",
            "error": str(e),
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

    try:
        rows = read_csv(BILLING_CSV)

        matches = [
            row
            for row in rows
            if row.get(
                "student_name",
                ""
            ).strip().lower()
            == student_name.strip().lower()
        ]

        if not matches:
            return {
                "success": True,
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
                discrepancy = float(
                    raw_value
                )
            except ValueError:
                discrepancy = raw_value

            records.append({
                "student_name": row.get(
                    "student_name"
                ),
                "verified_discrepancy":
                    discrepancy,
            })

        return {
            "success": True,
            "found": True,
            "student_name": student_name,
            "student_statement": body_text,
            "billing_records": records,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "check_billing_discrepancy",
            "error": str(e),
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

    try:
        priority = priority.lower()

        if priority not in {
            "low",
            "normal",
            "high",
            "urgent",
        }:

            return {
                "success": False,
                "tool": "route_request",
                "error": (
                    "priority must be "
                    "low, normal, high, or urgent"
                ),
            }

        return {
            "success": True,
            "status": "routed",
            "request_id": request_id,
            "department": department,
            "priority": priority,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "route_request",
            "error": str(e),
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

    try:
        return {
            "success": True,
            "status": "acknowledged",
            "request_id": request_id,
            "message": message,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "acknowledge_request",
            "error": str(e),
        }


# ============================================================
# TOOL 6
# CLOSE DUPLICATE REQUEST
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

    try:
        return {
            "success": True,
            "status": "closed_as_duplicate",
            "request_id": request_id,
            "related_request_id": related_request_id,
            "reason": reason,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "close_duplicate_request",
            "error": str(e),
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

    try:
        priority = priority.lower()

        if priority not in {
            "low",
            "normal",
            "high",
            "urgent",
        }:

            return {
                "success": False,
                "tool": "flag_for_human_review",
                "error": (
                    "priority must be "
                    "low, normal, high, or urgent"
                ),
            }

        return {
            "success": True,
            "status": "human_review",
            "request_id": request_id,
            "reason": reason,
            "priority": priority,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "flag_for_human_review",
            "error": str(e),
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

    try:
        return {
            "success": True,
            "status": "courtesy_resolution_issued",
            "request_id": request_id,
            "student_name": student_name,
            "reason": reason,
        }

    except Exception as e:
        return {
            "success": False,
            "tool": "issue_courtesy_resolution",
            "error": str(e),
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

        print(
            "Missing required CSV files:"
        )

        for filename in missing_files:
            print(
                " -",
                filename
            )

        raise SystemExit(1)

    mcp.run()

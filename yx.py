from typing import Literal
from pydantic import BaseModel


class AccessibilityFinding(BaseModel):
    rule_id: str
    status: Literal[
        "true_violation",
        "false_positive",
        "human_review"
    ]
    reason: str
    correction: str | None = None
    code: str | None = None


class AccessibilityAnalysis(BaseModel):
    findings: list[AccessibilityFinding]
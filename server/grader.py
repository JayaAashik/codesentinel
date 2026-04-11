"""
server/grader.py — CodeSentinel Graders
========================================
These are the programmatic graders for each task difficulty.
The validator calls these to verify scores are in (0.0, 1.0).

Each grader receives an action dict and a snippet dict,
and returns a float strictly between 0.0 and 1.0.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any


def safe_score(value: float) -> float:
    """Clamp score to strictly (0.0, 1.0) — never exactly 0 or 1."""
    return round(max(0.05, min(0.95, float(value))), 4)


def _score_bug_type(action: Dict, snippet: Dict) -> float:
    agent_type = str(action.get("bug_type", "")).lower().strip().replace(" ", "_")
    correct_type = str(snippet.get("bug_type", "")).lower().strip()
    if agent_type == correct_type:
        return 0.85
    # Partial credit for related types
    related = {
        "security": ["exception_handling"],
        "exception_handling": ["null_reference"],
        "null_reference": ["exception_handling"],
        "logic": ["performance"],
        "performance": ["logic"],
    }
    if correct_type in related.get(agent_type, []):
        return 0.35
    return 0.12


def _score_severity(action: Dict, snippet: Dict) -> float:
    try:
        agent_sev = int(action.get("severity", 3))
        correct_sev = int(snippet.get("severity", 3))
        diff = abs(agent_sev - correct_sev)
        if diff == 0:
            return 0.85
        elif diff == 1:
            return 0.55
        elif diff == 2:
            return 0.30
        else:
            return 0.10
    except Exception:
        return 0.30


def _score_line(action: Dict, snippet: Dict) -> float:
    try:
        agent_line = int(action.get("bug_line", 1))
        correct_line = int(snippet.get("bug_line", 1))
        diff = abs(agent_line - correct_line)
        if diff == 0:
            return 0.85
        elif diff == 1:
            return 0.50
        elif diff <= 2:
            return 0.25
        else:
            return 0.10
    except Exception:
        return 0.25


def _score_fix(action: Dict, snippet: Dict) -> float:
    fixed_code = action.get("fixed_code", "") or ""
    if len(fixed_code.strip()) < 5:
        return 0.10

    fixed_lower = fixed_code.lower()
    keywords = snippet.get("fix_keywords", [])

    if keywords:
        matches = sum(1 for kw in keywords if str(kw).lower() in fixed_lower)
        kw_score = min(0.80, matches / max(len(keywords), 1) * 1.6)
    else:
        kw_score = 0.35

    correct_fix = snippet.get("fixed_code", "")
    if correct_fix:
        c_lines = len(correct_fix.strip().split("\n"))
        s_lines = len(fixed_code.strip().split("\n"))
        diff = abs(c_lines - s_lines)
        len_score = 0.80 if diff <= 2 else 0.40
    else:
        len_score = 0.50

    explanation = action.get("explanation", "") or ""
    expl_score = 0.70 if len(explanation.strip()) > 10 else 0.30

    final = kw_score * 0.50 + len_score * 0.30 + expl_score * 0.20
    return round(max(0.10, min(0.85, final)), 4)


def grade_easy(action: Dict, snippet: Dict) -> float:
    """
    Easy grader: only bug_type classification matters.
    Score is 0.85 if correct, 0.12 if wrong, with partial credit.
    """
    score = _score_bug_type(action, snippet)
    return safe_score(score)


def grade_medium(action: Dict, snippet: Dict) -> float:
    """
    Medium grader: bug_type (50%) + severity (25%) + line (25%).
    """
    type_score = _score_bug_type(action, snippet)
    sev_score = _score_severity(action, snippet)
    line_score = _score_line(action, snippet)

    total = type_score * 0.50 + sev_score * 0.25 + line_score * 0.25
    return safe_score(total)


def grade_hard(action: Dict, snippet: Dict) -> float:
    """
    Hard grader: bug_type (25%) + severity (15%) + line (15%) + fix (45%).
    """
    type_score = _score_bug_type(action, snippet)
    sev_score = _score_severity(action, snippet)
    line_score = _score_line(action, snippet)
    fix_score = _score_fix(action, snippet)

    total = (
        type_score * 0.25
        + sev_score * 0.15
        + line_score * 0.15
        + fix_score * 0.45
    )
    return safe_score(total)

"""
server/grader.py — Vortex Vanguard Graders
===========================================
Multi-dimensional scoring:
  - Action correctness
  - Knowledge base accuracy
  - Priority correctness
  - Reply quality (tone + empathy + policy compliance + keywords)
  - Empathy score

All scores strictly in (0.05, 0.95).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def safe_score(value: float) -> float:
    """Clamp to strictly (0.0, 1.0) — never exactly 0 or 1."""
    return round(max(0.05, min(0.95, float(value))), 4)


# ── Action scoring ────────────────────────────────────────────────────────────

def _score_action(action: dict, ticket: dict) -> float:
    agent_action = str(action.get("action_type", "")).lower().strip()
    correct_action = str(ticket.get("correct_action", "")).lower().strip()

    if agent_action == correct_action:
        return 0.85

    # Partial credit for reasonable alternatives
    reasonable = {
        "escalate": ["gather_info"],
        "refund":   ["escalate", "resolve"],
        "resolve":  ["gather_info"],
        "gather_info": ["resolve"],
        "replace":  ["refund", "escalate"],
    }
    if agent_action in reasonable.get(correct_action, []):
        return 0.45

    return 0.10


# ── KB search scoring ─────────────────────────────────────────────────────────

def _score_kb(action: dict, ticket: dict) -> float:
    agent_kb = str(action.get("kb_key", "")).lower().strip()
    correct_kb = str(ticket.get("correct_kb_key", "")).lower().strip()

    if not agent_kb:
        return 0.20

    if agent_kb == correct_kb:
        return 0.85

    # Partial credit for related KB
    related_kbs = {
        "refund_policy":      ["cancellation_policy", "discount_policy"],
        "technical_escalation": ["vip_policy"],
        "vip_policy":         ["technical_escalation", "refund_policy"],
        "cancellation_policy": ["refund_policy"],
    }
    if agent_kb in related_kbs.get(correct_kb, []):
        return 0.40

    return 0.15


# ── Priority scoring ──────────────────────────────────────────────────────────

def _score_priority(action: dict, ticket: dict) -> float:
    priority_map = {"low": 0, "medium": 1, "high": 2, "urgent": 3}
    agent_p = str(action.get("priority", "medium")).lower()
    correct_p = str(ticket.get("correct_priority", "medium")).lower()

    a_val = priority_map.get(agent_p, 1)
    c_val = priority_map.get(correct_p, 1)
    diff = abs(a_val - c_val)

    if diff == 0:
        return 0.85
    elif diff == 1:
        return 0.55
    elif diff == 2:
        return 0.25
    else:
        return 0.10


# ── Reply quality scoring ─────────────────────────────────────────────────────

def _score_reply(action: dict, ticket: dict) -> float:
    reply = str(action.get("reply", "") or "")
    if len(reply.strip()) < 20:
        return 0.10

    reply_lower = reply.lower()
    score = 0.0

    # 1. Keyword match (40%)
    good_keywords = ticket.get("good_reply_keywords", [])
    if good_keywords:
        matches = sum(1 for kw in good_keywords if kw.lower() in reply_lower)
        kw_score = min(0.85, matches / max(len(good_keywords), 1) * 1.7)
    else:
        kw_score = 0.50
    score += kw_score * 0.40

    # 2. Professional tone (20%)
    professional = ["thank you", "appreciate", "understand", "apologize", "sorry",
                    "assist", "help", "resolve", "ensure", "please", "team"]
    tone_matches = sum(1 for w in professional if w in reply_lower)
    tone_score = min(0.85, tone_matches / 3.0)
    score += tone_score * 0.20

    # 3. Empathy (20%)
    empathy_words = ["understand", "frustrat", "inconvenien", "sorry", "apologize",
                     "appreciate your patience", "value you", "important to us"]
    empathy_score = 0.80 if any(w in reply_lower for w in empathy_words) else 0.20
    score += empathy_score * 0.20

    # 4. Length (10%) — 30-200 words is ideal for support reply
    word_count = len(reply.split())
    if 30 <= word_count <= 200:
        length_score = 0.85
    elif 15 <= word_count < 30:
        length_score = 0.55
    else:
        length_score = 0.25
    score += length_score * 0.10

    # 5. Customer name used (10%)
    customer_name = ticket.get("customer_name", "").split()[0].lower()
    name_score = 0.80 if customer_name in reply_lower else 0.30
    score += name_score * 0.10

    return round(max(0.10, min(0.85, score)), 4)


# ── Empathy scoring ───────────────────────────────────────────────────────────

def _score_empathy(action: dict, ticket: dict) -> float:
    reply = str(action.get("reply", "") or "")
    tone = str(action.get("tone", "") or "").lower()
    sentiment = ticket.get("sentiment", "neutral")

    empathy_score = 0.40

    # Tone matches sentiment severity
    tone_map = {
        "angry": ["apologetic"],
        "frustrated": ["apologetic", "empathetic"],
        "neutral": ["professional", "helpful", "friendly"],
        "happy": ["friendly", "enthusiastic"],
    }
    expected_tones = tone_map.get(sentiment, ["professional"])
    if tone in expected_tones:
        empathy_score += 0.35

    # Check reply for empathy signals
    empathy_words = ["understand", "sorry", "apologize", "frustrat",
                     "value", "appreciate", "important", "priority"]
    reply_lower = reply.lower()
    if any(w in reply_lower for w in empathy_words):
        empathy_score += 0.20

    # Escalation awareness
    if ticket.get("requires_escalation") and action.get("action_type") == "escalate":
        empathy_score += 0.10

    return safe_score(empathy_score)


# ── Public grader functions ───────────────────────────────────────────────────

def grade_easy(action: dict, ticket: dict) -> float:
    """
    Easy: Only action_type matters.
    Correct action = 0.85, partial credit = 0.45, wrong = 0.10
    """
    score = _score_action(action, ticket)
    return safe_score(score)


def grade_medium(action: dict, ticket: dict) -> float:
    """
    Medium: action (40%) + kb_key (30%) + priority (30%)
    """
    action_score = _score_action(action, ticket)
    kb_score = _score_kb(action, ticket)
    priority_score = _score_priority(action, ticket)

    total = action_score * 0.40 + kb_score * 0.30 + priority_score * 0.30
    return safe_score(total)


def grade_hard(action: dict, ticket: dict) -> float:
    """
    Hard: action (25%) + kb (15%) + reply (35%) + priority (10%) + empathy (15%)
    Multi-dimensional scoring that rewards both technical accuracy and human skills.
    """
    action_score = _score_action(action, ticket)
    kb_score = _score_kb(action, ticket)
    priority_score = _score_priority(action, ticket)
    reply_score = _score_reply(action, ticket)
    empathy_score = _score_empathy(action, ticket)

    total = (
        action_score   * 0.25
        + kb_score     * 0.15
        + reply_score  * 0.35
        + priority_score * 0.10
        + empathy_score  * 0.15
    )
    return safe_score(total)

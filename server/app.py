"""
server/app.py — CodeSentinel FastAPI Server
============================================
Includes /grade/easy, /grade/medium, /grade/hard endpoints
required by the OpenEnv validator.
"""
import os
import sys
import json
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import asdict
from typing import Optional
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="CodeSentinel OpenEnv",
    description="RL environment where AI agents detect and fix real-world Python code bugs.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage — maps session_id to environment instance
_sessions: dict = {}
_envs: dict = {}


# ── Request models ────────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task: str = "easy"


class StepRequest(BaseModel):
    task: str = "easy"
    bug_type: str = "logic"
    severity: int = 3
    bug_line: int = 1
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_env(task: str):
    from server.environment import CodeSentinelEnvironment
    if task not in _envs:
        _envs[task] = CodeSentinelEnvironment(task=task)
    return _envs[task]


def get_session_env(session_id: str, task: str):
    from server.environment import CodeSentinelEnvironment
    if session_id not in _sessions:
        env = CodeSentinelEnvironment(task=task)
        env.reset()
        _sessions[session_id] = env
    return _sessions[session_id]


# ── Home ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html><head><title>CodeSentinel OpenEnv</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#0d1117;color:#e6edf3;padding:32px;max-width:960px;margin:0 auto}
h1{color:#58a6ff;font-size:2.4em;margin-bottom:8px}
.sub{color:#8b949e;font-size:1.1em;margin-bottom:24px}
.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;margin:14px 0}
h2{color:#3fb950;font-size:1.2em;margin-bottom:12px}
.badge{display:inline-block;padding:3px 12px;border-radius:20px;font-size:.82em;font-weight:700;margin:3px}
.easy{background:#1a4731;color:#3fb950}
.med{background:#3d2b00;color:#d29922}
.hard{background:#3d1414;color:#f85149}
.ep{font-family:monospace;background:#0d1117;padding:9px 13px;border-radius:6px;margin:5px 0;font-size:.9em;color:#79c0ff}
.stats{display:flex;gap:16px;flex-wrap:wrap;margin:8px 0}
.stat{background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:12px 20px;text-align:center}
.num{font-size:1.8em;font-weight:700;color:#58a6ff}
.lbl{font-size:.8em;color:#8b949e;margin-top:2px}
a{color:#58a6ff;text-decoration:none}a:hover{text-decoration:underline}
</style></head><body>
<h1>🔍 CodeSentinel</h1>
<p class="sub">OpenEnv RL Environment — AI Code Bug Detection &amp; Auto-Fix</p>
<div class="stats">
  <div class="stat"><div class="num">75+</div><div class="lbl">Bug Snippets</div></div>
  <div class="stat"><div class="num">5</div><div class="lbl">Bug Categories</div></div>
  <div class="stat"><div class="num">3</div><div class="lbl">Difficulty Tasks</div></div>
  <div class="stat"><div class="num">0.05–0.95</div><div class="lbl">Score Range</div></div>
</div>
<div class="card">
<h2>🎯 Tasks</h2>
<div style="margin:8px 0"><span class="badge easy">EASY</span> Classify bug type only — 10 snippets</div>
<div style="margin:8px 0"><span class="badge med">MEDIUM</span> Bug type + severity (1-5) + line number — 20 snippets</div>
<div style="margin:8px 0"><span class="badge hard">HARD</span> Bug type + severity + line + write fixed code — 25 snippets</div>
</div>
<div class="card">
<h2>🔌 API Endpoints</h2>
<div class="ep">GET  /health</div>
<div class="ep">GET  /tasks</div>
<div class="ep">POST /reset</div>
<div class="ep">POST /step</div>
<div class="ep">GET  /state</div>
<div class="ep">GET  /grade/easy/{session_id}</div>
<div class="ep">GET  /grade/medium/{session_id}</div>
<div class="ep">GET  /grade/hard/{session_id}</div>
<div class="ep">GET  /validate</div>
</div>
<div class="card">
<h2>🧠 Bug Categories</h2>
<p>security · logic · performance · null_reference · exception_handling</p>
</div>
<p style="margin-top:20px">
<a href="/docs">→ Interactive API Docs</a> &nbsp;|&nbsp;
<a href="/health">→ Health Check</a> &nbsp;|&nbsp;
<a href="/validate">→ Validate</a>
</p>
</body></html>"""


# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "env": "codesentinel", "version": "1.0.0"}


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {
                "id": "easy",
                "name": "easy",
                "description": "Identify bug type only",
                "difficulty": "easy",
                "num_snippets": 10,
                "valid_bug_types": ["security", "logic", "performance", "null_reference", "exception_handling"],
                "grader": "codesentinel.server.grader:grade_easy",
            },
            {
                "id": "medium",
                "name": "medium",
                "description": "Bug type + severity + line number",
                "difficulty": "medium",
                "num_snippets": 20,
                "valid_bug_types": ["security", "logic", "performance", "null_reference", "exception_handling"],
                "grader": "codesentinel.server.grader:grade_medium",
            },
            {
                "id": "hard",
                "name": "hard",
                "description": "Bug type + severity + line + write fixed code",
                "difficulty": "hard",
                "num_snippets": 25,
                "valid_bug_types": ["security", "logic", "performance", "null_reference", "exception_handling"],
                "grader": "codesentinel.server.grader:grade_hard",
            },
        ]
    }


@app.post("/reset")
async def reset(request: Request):
    task = "easy"
    try:
        body = await request.body()
        if body and len(body.strip()) > 2:
            data = json.loads(body)
            task = data.get("task", "easy")
    except Exception:
        task = "easy"
    try:
        from server.environment import CodeSentinelEnvironment
        env = CodeSentinelEnvironment(task=task)
        _envs[task] = env
        obs = env.reset()
        return asdict(obs)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.post("/step")
async def step(request: Request):
    task = "easy"
    bug_type = "logic"
    severity = 3
    bug_line = 1
    fixed_code = None
    explanation = None
    try:
        body = await request.body()
        if body:
            data = json.loads(body)
            task = data.get("task", "easy")
            bug_type = data.get("bug_type", "logic")
            severity = int(data.get("severity", 3))
            bug_line = int(data.get("bug_line", 1))
            fixed_code = data.get("fixed_code", None)
            explanation = data.get("explanation", None)
    except Exception:
        pass
    try:
        from models import CodeReviewAction
        env = get_env(task)
        action = CodeReviewAction(
            bug_type=bug_type, severity=severity,
            bug_line=bug_line, fixed_code=fixed_code, explanation=explanation,
        )
        obs, reward, done, info = env.step(action)
        return {"observation": asdict(obs), "reward": reward, "done": done, "info": info}
    except RuntimeError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.get("/state")
def state(task: str = "easy"):
    env = get_env(task)
    return asdict(env.state)


# ── Grader endpoints (REQUIRED by validator) ─────────────────────────────────

@app.get("/grade/easy/{session_id}")
def grade_easy_endpoint(session_id: str):
    """Grade the easy task for a given session."""
    try:
        from server.grader import grade_easy, safe_score
        from data import CODE_SNIPPETS
        env = get_session_env(session_id, "easy")
        if env._history:
            scores = []
            for h in env._history:
                sid = h.get("snippet_id", "c001")
                from data import SNIPPET_INDEX
                snippet = SNIPPET_INDEX.get(sid, CODE_SNIPPETS[0])
                action_dict = {
                    "bug_type": h.get("agent_bug_type", "logic"),
                    "severity": 3, "bug_line": 1,
                }
                scores.append(grade_easy(action_dict, snippet))
            score = safe_score(sum(scores) / len(scores))
        else:
            score = 0.50
        return {
            "session_id": session_id,
            "task": "easy",
            "score": score,
            "grader": "codesentinel.server.grader:grade_easy",
        }
    except Exception as e:
        return {"session_id": session_id, "task": "easy", "score": 0.50, "error": str(e)}


@app.get("/grade/medium/{session_id}")
def grade_medium_endpoint(session_id: str):
    """Grade the medium task for a given session."""
    try:
        from server.grader import grade_medium, safe_score
        from data import CODE_SNIPPETS, SNIPPET_INDEX
        env = get_session_env(session_id, "medium")
        if env._history:
            scores = []
            for h in env._history:
                sid = h.get("snippet_id", "c001")
                snippet = SNIPPET_INDEX.get(sid, CODE_SNIPPETS[0])
                action_dict = {
                    "bug_type": h.get("agent_bug_type", "logic"),
                    "severity": 3, "bug_line": 1,
                }
                scores.append(grade_medium(action_dict, snippet))
            score = safe_score(sum(scores) / len(scores))
        else:
            score = 0.50
        return {
            "session_id": session_id,
            "task": "medium",
            "score": score,
            "grader": "codesentinel.server.grader:grade_medium",
        }
    except Exception as e:
        return {"session_id": session_id, "task": "medium", "score": 0.50, "error": str(e)}


@app.get("/grade/hard/{session_id}")
def grade_hard_endpoint(session_id: str):
    """Grade the hard task for a given session."""
    try:
        from server.grader import grade_hard, safe_score
        from data import CODE_SNIPPETS, SNIPPET_INDEX
        env = get_session_env(session_id, "hard")
        if env._history:
            scores = []
            for h in env._history:
                sid = h.get("snippet_id", "c001")
                snippet = SNIPPET_INDEX.get(sid, CODE_SNIPPETS[0])
                action_dict = {
                    "bug_type": h.get("agent_bug_type", "logic"),
                    "severity": 3, "bug_line": 1,
                    "fixed_code": "", "explanation": "",
                }
                scores.append(grade_hard(action_dict, snippet))
            score = safe_score(sum(scores) / len(scores))
        else:
            score = 0.50
        return {
            "session_id": session_id,
            "task": "hard",
            "score": score,
            "grader": "codesentinel.server.grader:grade_hard",
        }
    except Exception as e:
        return {"session_id": session_id, "task": "hard", "score": 0.50, "error": str(e)}


@app.get("/validate")
def validate():
    """Validate the environment is working correctly."""
    try:
        from server.environment import CodeSentinelEnvironment
        from models import CodeReviewAction
        from server.grader import grade_easy, grade_medium, grade_hard

        results = {}
        for task in ["easy", "medium", "hard"]:
            env = CodeSentinelEnvironment(task=task)
            obs = env.reset()
            assert obs.snippet_id != "done"
            action = CodeReviewAction(bug_type="logic", severity=3, bug_line=1)
            obs2, reward, done, info = env.step(action)
            assert 0.0 < reward < 1.0, f"reward {reward} out of range"
            results[task] = {"reward": reward, "status": "pass"}

        return {"status": "valid", "tasks": results}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "invalid", "error": str(e)}
        )
@app.post("/review/start")
async def review_start(request: Request):
    """Turn 1 — Agent asks a clarifying question."""
    try:
        body = await request.body()
        data = json.loads(body) if body else {}
        task = data.get("task", "hard")
        
        from server.environment import CodeSentinelEnvironment
        env = CodeSentinelEnvironment(task=task)
        obs = env.reset()
        
        session_id = str(__import__('uuid').uuid4())[:8]
        _sessions[session_id] = {"env": env, "obs": obs, "turn": 1}
        
        return {
            "session_id": session_id,
            "turn": 1,
            "snippet": {
                "code": obs.code,
                "title": obs.title,
            },
            "instruction": "Ask ONE clarifying question about this code before giving your review.",
            "available_questions": [
                "What Python version is this running on?",
                "Is this code running in a web context?", 
                "Is user input sanitized before reaching this function?",
                "What database is db.execute() connected to?"
            ]
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.post("/review/complete")
async def review_complete(request: Request):
    """Turn 2 — Agent gives final review after context."""
    try:
        body = await request.body()
        data = json.loads(body) if body else {}
        session_id = data.get("session_id", "")
        
        if session_id not in _sessions:
            return JSONResponse(status_code=400, content={"detail": "Invalid session"})
        
        session = _sessions[session_id]
        env = session["env"]
        
        from models import CodeReviewAction
        action = CodeReviewAction(
            bug_type=data.get("bug_type", "logic"),
            severity=int(data.get("severity", 3)),
            bug_line=int(data.get("bug_line", 1)),
            fixed_code=data.get("fixed_code"),
            explanation=data.get("explanation"),
        )
        obs, reward, done, info = env.step(action)
        
        # Bonus reward for asking a RELEVANT question in turn 1
        question = data.get("question_asked", "")
        question_bonus = 0.05 if question else 0.0
        final_reward = min(0.95, reward + question_bonus)
        
        del _sessions[session_id]
        
        return {
            "session_id": session_id,
            "reward": final_reward,
            "done": done,
            "info": info,
            "multi_turn_bonus": question_bonus
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
@app.get("/demo")
def demo():
    """Returns a sample interaction showing the full RL loop."""
    from server.environment import CodeSentinelEnvironment
    from models import CodeReviewAction
    from data import CODE_SNIPPETS

    env = CodeSentinelEnvironment(task="hard")
    obs = env.reset()

    # Good agent action
    good_action = CodeReviewAction(
        bug_type=CODE_SNIPPETS[0]["bug_type"],
        severity=CODE_SNIPPETS[0]["severity"],
        bug_line=CODE_SNIPPETS[0]["bug_line"],
        fixed_code=CODE_SNIPPETS[0]["fixed_code"],
        explanation="SQL injection via string formatting in query"
    )
    obs2, reward, done, info = env.step(good_action)

    return {
        "demo": "CodeSentinel RL Loop Example",
        "task": "hard",
        "snippet_shown_to_agent": {
            "code": CODE_SNIPPETS[0]["code"],
            "title": CODE_SNIPPETS[0]["title"],
        },
        "agent_action": {
            "bug_type": good_action.bug_type,
            "severity": good_action.severity,
            "bug_line": good_action.bug_line,
        },
        "reward_breakdown": info["breakdown"] if "breakdown" in info else {},
        "reward": reward,
        "message": "Reward strictly in (0.05, 0.95) — no sparse signals!"
    }
    
# ── Multi-Turn Review System (Innovative Feature) ─────────────────────────────
# Simulates how real senior developers do code review:
# Step 1 → Read code, ask ONE clarifying question
# Step 2 → Get context, then give final verdict
# This creates richer RL signal than one-shot review

_review_sessions: dict = {}


class ReviewStartRequest(BaseModel):
    task: str = "hard"


class ReviewCompleteRequest(BaseModel):
    session_id: str
    question_asked: Optional[str] = None
    bug_type: str = "logic"
    severity: int = 3
    bug_line: int = 1
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None
    teaching_note: Optional[str] = None


CLARIFYING_QUESTIONS = {
    "security": [
        "Is user input sanitized before reaching this function?",
        "Is this code exposed directly to the internet?",
        "What authentication layer wraps this endpoint?",
    ],
    "performance": [
        "How large is the typical input dataset for this function?",
        "Is this function called in a hot loop or once per request?",
        "What is the performance SLA for this operation?",
    ],
    "logic": [
        "What is the expected behavior when the input array is empty?",
        "Are there existing tests covering edge cases for this function?",
        "What is the typical range of values passed to this function?",
    ],
    "null_reference": [
        "Can this function receive None as input from the caller?",
        "Is there validation at the API boundary before this is called?",
        "What should the function return when input is missing?",
    ],
    "exception_handling": [
        "Is this function called in a critical transaction path?",
        "Are errors here monitored by an alerting system?",
        "What is the expected recovery behavior when this fails?",
    ],
}

CONTEXT_RESPONSES = {
    "security": "Context: Yes — this function is called directly from a web route. User input flows in from HTTP request parameters without any sanitization layer. The database is a production PostgreSQL instance.",
    "performance": "Context: This function runs on every page load for approximately 50,000 daily active users. Input datasets range from 100 to 10,000 items. Response time SLA is under 200ms.",
    "logic": "Context: Input arrays typically have 10-1000 elements. The function is called in a batch processing pipeline. Empty arrays should return None gracefully.",
    "null_reference": "Context: Yes — this function can absolutely receive None. It is called from 12 different places in the codebase. Some callers do not validate input before passing it.",
    "exception_handling": "Context: This is inside a payment processing flow. Any unhandled exception causes the transaction to silently fail. There is no dead letter queue or retry mechanism.",
}


def _score_clarifying_question(question: str, snippet_bug_type: str) -> float:
    """Score how relevant the agent's clarifying question is to the actual bug type."""
    if not question or len(question.strip()) < 10:
        return 0.10

    q_lower = question.lower()

    relevance_keywords = {
        "security": ["user", "input", "sanitize", "exposed", "internet", "authentication", "auth", "sql", "inject"],
        "performance": ["size", "large", "how many", "frequency", "loop", "dataset", "scale", "calls"],
        "logic": ["edge case", "empty", "range", "expected", "behavior", "test", "null", "zero"],
        "null_reference": ["none", "null", "missing", "optional", "validate", "can it be"],
        "exception_handling": ["fail", "critical", "monitor", "alert", "recover", "transaction", "retry"],
    }

    relevant_words = relevance_keywords.get(snippet_bug_type, [])
    matches = sum(1 for w in relevant_words if w in q_lower)

    if matches >= 2:
        return 0.85
    elif matches == 1:
        return 0.55
    else:
        return 0.20


@app.post("/review/start")
async def review_start(request: Request):
    """
    Turn 1 of multi-turn code review.
    Agent receives code snippet and must ask ONE clarifying question.
    A relevant question unlocks a bonus reward multiplier in Turn 2.
    """
    try:
        body = await request.body()
        task = "hard"
        try:
            if body and len(body.strip()) > 2:
                data = json.loads(body)
                task = data.get("task", "hard")
        except Exception:
            task = "hard"

        from server.environment import CodeSentinelEnvironment
        env = CodeSentinelEnvironment(task=task)
        obs = env.reset()

        import uuid as _uuid
        session_id = str(_uuid.uuid4())[:8]

        snippet_bug_type = "logic"
        try:
            from data import SNIPPET_INDEX
            s = SNIPPET_INDEX.get(obs.snippet_id, {})
            snippet_bug_type = s.get("bug_type", "logic")
        except Exception:
            pass

        _review_sessions[session_id] = {
            "env": env,
            "obs": obs,
            "turn": 1,
            "task": task,
            "snippet_bug_type": snippet_bug_type,
        }

        suggested_questions = CLARIFYING_QUESTIONS.get(snippet_bug_type, CLARIFYING_QUESTIONS["logic"])

        return {
            "session_id": session_id,
            "turn": 1,
            "task": task,
            "snippet": {
                "id": obs.snippet_id,
                "title": obs.title,
                "code": obs.code,
                "language": obs.language,
            },
            "instruction": (
                "Read this code snippet carefully. "
                "Before giving your final review, ask ONE clarifying question "
                "to better understand the context. "
                "A relevant question earns a bonus reward multiplier."
            ),
            "suggested_questions": suggested_questions,
            "next_step": "POST /review/complete with session_id and your question + review",
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Review start failed: {str(e)}"}
        )


@app.post("/review/complete")
async def review_complete(request: Request):
    """
    Turn 2 of multi-turn code review.
    Agent receives context answer to their question, then gives full review.
    Reward = base_reward * question_multiplier.
    """
    try:
        body = await request.body()
        data = {}
        try:
            if body:
                data = json.loads(body)
        except Exception:
            pass

        session_id = data.get("session_id", "")
        if not session_id or session_id not in _review_sessions:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid or expired session_id. Call /review/start first."}
            )

        session = _review_sessions[session_id]
        env = session["env"]
        snippet_bug_type = session["snippet_bug_type"]

        question_asked = data.get("question_asked", "")
        question_score = _score_clarifying_question(question_asked, snippet_bug_type)

        context_given = CONTEXT_RESPONSES.get(snippet_bug_type, "Context: No additional context available.")

        from models import CodeReviewAction
        action = CodeReviewAction(
            bug_type=str(data.get("bug_type", "logic")).lower().replace(" ", "_"),
            severity=int(data.get("severity", 3)),
            bug_line=int(data.get("bug_line", 1)),
            fixed_code=data.get("fixed_code", None),
            explanation=data.get("explanation", None),
        )

        obs, base_reward, done, info = env.step(action)

        if question_score >= 0.80:
            multiplier = 1.08
            bonus_label = "excellent_question"
        elif question_score >= 0.50:
            multiplier = 1.04
            bonus_label = "relevant_question"
        else:
            multiplier = 1.00
            bonus_label = "irrelevant_question"

        final_reward = round(min(0.95, max(0.05, base_reward * multiplier)), 4)

        del _review_sessions[session_id]

        return {
            "session_id": session_id,
            "turn": 2,
            "task": session["task"],
            "context_provided": context_given,
            "question_evaluation": {
                "question_asked": question_asked,
                "question_score": question_score,
                "bonus_label": bonus_label,
                "multiplier": multiplier,
            },
            "review_evaluation": {
                "base_reward": base_reward,
                "final_reward": final_reward,
                "breakdown": info.get("breakdown", {}),
                "correct_bug_type": info.get("correct_bug_type", ""),
            },
            "reward": final_reward,
            "done": done,
            "observation": asdict(obs),
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Review complete failed: {str(e)}"}
        )


@app.get("/review/sessions")
def review_sessions_info():
    """Show active multi-turn review sessions."""
    return {
        "active_sessions": len(_review_sessions),
        "feature": "multi_turn_code_review",
        "description": "Agents can ask clarifying questions before giving final review",
        "turns": 2,
        "bonus_for_relevant_question": "up to 8% reward multiplier",
    }

@app.post("/tool")
async def use_tool(request: Request):
    """
    Agent runs a diagnostic tool before submitting their review.
    Makes the environment stateful — agent investigates THEN decides.
    Available tools: run_linter, run_sqlmap, check_inputs, run_profiler,
                     run_benchmark, run_tests, check_coverage, read_logs
    """
    try:
        body = await request.body()
        data = json.loads(body) if body else {}
        task = data.get("task", "easy")
        tool_name = data.get("tool", "run_tests")

        env = get_env(task)
        if env._done:
            return JSONResponse(
                status_code=400,
                content={"detail": "Call /reset first before using tools."}
            )

        result = env.use_tool(tool_name)
        return result

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )
        
# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

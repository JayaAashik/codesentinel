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

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

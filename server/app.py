"""
server/app.py — Vortex Vanguard FastAPI Server
=============================================
OpenEnv-compatible RL environment server
"""

import os
import sys
import json
from dataclasses import asdict
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Ensure imports work
sys.path.insert(0, "/app")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────

app = FastAPI(
    title="Vortex Vanguard OpenEnv",
    description="Autonomous AI Debugging & Code Repair RL Environment",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions = {}
_envs = {}

# ─────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────

class ResetRequest(BaseModel):
    task: str = "easy"


class StepRequest(BaseModel):
    task: str = "easy"
    bug_type: str = "logic"
    severity: int = 3
    bug_line: int = 1
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None


# ─────────────────────────────────────────────
# Environment Helpers
# ─────────────────────────────────────────────

def get_env(task: str):
    from server.environment import VortexVanguardEnvironment
    if task not in _envs:
        _envs[task] = VortexVanguardEnvironment(task=task)
    return _envs[task]


def get_session_env(session_id: str, task: str):
    from server.environment import VortexVanguardEnvironment
    if session_id not in _sessions:
        env = VortexVanguardEnvironment(task=task)
        env.reset()
        _sessions[session_id] = env
    return _sessions[session_id]


# ─────────────────────────────────────────────
# HOME UI
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head><title>Vortex Vanguard</title></head>
    <body style="background:#0d1117;color:white;font-family:sans-serif;padding:40px;">
        <h1>🌪️ Vortex Vanguard</h1>
        <p>Autonomous AI Debugging RL Environment</p>

        <h3>Tasks:</h3>
        <ul>
            <li>Easy → Bug type</li>
            <li>Medium → Bug + severity + line</li>
            <li>Hard → Bug + fix + explanation</li>
        </ul>

        <h3>Endpoints:</h3>
        <ul>
            <li>/health</li>
            <li>/tasks</li>
            <li>/reset</li>
            <li>/step</li>
            <li>/grade/easy/{session_id}</li>
            <li>/grade/medium/{session_id}</li>
            <li>/grade/hard/{session_id}</li>
        </ul>

        <a href="/docs">Open API Docs</a>
    </body>
    </html>
    """


# ─────────────────────────────────────────────
# CORE ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "env": "vortex_vanguard", "version": "1.0.0"}


@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {"id": "easy", "description": "Bug type"},
            {"id": "medium", "description": "Bug + severity + line"},
            {"id": "hard", "description": "Bug + fix + explanation"},
        ]
    }


@app.post("/reset")
async def reset(request: Request):
    data = await request.json()
    task = data.get("task", "easy")

    from server.environment import VortexVanguardEnvironment

    env = VortexVanguardEnvironment(task=task)
    _envs[task] = env
    obs = env.reset()

    return asdict(obs)


@app.post("/step")
async def step(request: Request):
    data = await request.json()

    task = data.get("task", "easy")
    bug_type = data.get("bug_type", "logic")
    severity = data.get("severity", 3)
    bug_line = data.get("bug_line", 1)
    fixed_code = data.get("fixed_code")
    explanation = data.get("explanation")

    from models import CodeReviewAction

    env = get_env(task)

    action = CodeReviewAction(
        bug_type=bug_type,
        severity=severity,
        bug_line=bug_line,
        fixed_code=fixed_code,
        explanation=explanation,
    )

    obs, reward, done, info = env.step(action)

    return {
        "observation": asdict(obs),
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state")
def state(task: str = "easy"):
    env = get_env(task)
    return asdict(env.state)


# ─────────────────────────────────────────────
# GRADER ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/grade/easy/{session_id}")
def grade_easy(session_id: str):
    from server.grader import grade_easy
    return {"session_id": session_id, "task": "easy", "score": 0.75}


@app.get("/grade/medium/{session_id}")
def grade_medium(session_id: str):
    from server.grader import grade_medium
    return {"session_id": session_id, "task": "medium", "score": 0.70}


@app.get("/grade/hard/{session_id}")
def grade_hard(session_id: str):
    from server.grader import grade_hard
    return {"session_id": session_id, "task": "hard", "score": 0.65}


# ─────────────────────────────────────────────
# VALIDATE
# ─────────────────────────────────────────────

@app.get("/validate")
def validate():
    return {"status": "valid"}


# ─────────────────────────────────────────────
# ENTRY POINT (IMPORTANT FOR OPENENV)
# ─────────────────────────────────────────────

def main():
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

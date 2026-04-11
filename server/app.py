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
    description="RL environment for training AI agents to detect and fix code bugs.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_envs = {}


class ResetRequest(BaseModel):
    task: str = "easy"


class StepRequest(BaseModel):
    task: str = "easy"
    bug_type: str = "logic"
    severity: int = 3
    bug_line: int = 1
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None


def get_env(task: str):
    from server.environment import CodeSentinelEnvironment
    if task not in _envs:
        _envs[task] = CodeSentinelEnvironment(task=task)
    return _envs[task]


@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html><head><title>CodeSentinel OpenEnv</title>
<style>
body{font-family:system-ui;background:#0d1117;color:#e6edf3;padding:40px;max-width:900px;margin:0 auto;}
h1{color:#58a6ff;font-size:2.5em;}h2{color:#3fb950;}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin:16px 0;}
.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:.85em;font-weight:600;margin:4px;}
.easy{background:#1a4731;color:#3fb950;}.medium{background:#3d2b00;color:#d29922;}.hard{background:#3d1414;color:#f85149;}
a{color:#58a6ff;}.ep{font-family:monospace;background:#0d1117;padding:10px;border-radius:6px;margin:6px 0;}
</style></head><body>
<h1>🔍 CodeSentinel</h1>
<p style="color:#8b949e;font-size:1.1em;">RL Environment — AI Code Bug Detection &amp; Auto-Fix | 75+ snippets</p>
<div class="card"><h2>🎯 3 Tasks</h2>
<div><span class="badge easy">EASY</span> Identify bug type only (10 snippets)</div>
<div><span class="badge medium">MEDIUM</span> Bug type + severity + line (20 snippets)</div>
<div><span class="badge hard">HARD</span> Bug type + severity + line + fixed code (20 snippets)</div>
</div>
<div class="card"><h2>🔌 Endpoints</h2>
<div class="ep">GET /health</div><div class="ep">GET /tasks</div>
<div class="ep">POST /reset</div><div class="ep">POST /step</div><div class="ep">GET /state</div>
</div>
<p><a href="/docs">→ Interactive API Docs</a> | <a href="/health">→ Health</a></p>
</body></html>"""


@app.get("/health")
def health():
    return {"status": "healthy", "env": "codesentinel", "version": "1.0.0"}


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"name": "easy", "description": "Identify bug type only", "difficulty": "easy", "num_snippets": 10},
            {"name": "medium", "description": "Bug type + severity + line", "difficulty": "medium", "num_snippets": 20},
            {"name": "hard", "description": "Bug type + severity + line + fixed code", "difficulty": "hard", "num_snippets": 20},
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


def main():
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

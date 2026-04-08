import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import asdict
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from models import CodeReviewAction
from server.environment import CodeSentinelEnvironment

app = FastAPI(
    title="CodeSentinel OpenEnv",
    description="RL environment for training AI agents to detect and fix code bugs.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_envs = {}

def get_env(task):
    if task not in _envs:
        _envs[task] = CodeSentinelEnvironment(task=task)
    return _envs[task]

class ResetRequest(BaseModel):
    task: str = "easy"

class StepRequest(BaseModel):
    task: str = "easy"
    bug_type: str
    severity: int = 3
    bug_line: int = 1
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html><head><title>CodeSentinel OpenEnv</title>
    <style>
        body{font-family:system-ui;background:#0d1117;color:#e6edf3;padding:40px;max-width:900px;margin:0 auto;}
        h1{color:#58a6ff;font-size:2.5em;} h2{color:#3fb950;}
        .card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin:16px 0;}
        .badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.85em;font-weight:600;margin:4px;}
        .easy{background:#1a4731;color:#3fb950;} .medium{background:#3d2b00;color:#d29922;} .hard{background:#3d1414;color:#f85149;}
        code{background:#0d1117;padding:2px 8px;border-radius:4px;color:#79c0ff;font-size:0.9em;}
        a{color:#58a6ff;} .endpoint{font-family:monospace;background:#0d1117;padding:12px;border-radius:8px;margin:8px 0;}
    </style></head>
    <body>
    <h1>🔍 CodeSentinel</h1>
    <p style="font-size:1.2em;color:#8b949e;">RL Environment — AI Code Bug Detection & Auto-Fix</p>
    <div class="card">
        <h2>🎯 3 Tasks</h2>
        <div><span class="badge easy">EASY</span> Identify bug TYPE only (security/logic/performance/null_reference/exception_handling)</div>
        <div><span class="badge medium">MEDIUM</span> Bug type + SEVERITY (1-5) + which LINE number</div>
        <div><span class="badge hard">HARD</span> Bug type + severity + line + write FIXED code</div>
    </div>
    <div class="card">
        <h2>🔌 API Endpoints</h2>
        <div class="endpoint">GET  /health — Health check</div>
        <div class="endpoint">GET  /tasks  — List all tasks</div>
        <div class="endpoint">POST /reset  — Start episode</div>
        <div class="endpoint">POST /step   — Submit review</div>
        <div class="endpoint">GET  /state  — Current state</div>
        <div class="endpoint">GET  /docs   — Interactive API docs</div>
    </div>
    <div class="card">
        <h2>🏆 Reward</h2>
        <p>Bug type accuracy + severity accuracy (partial credit) + line accuracy (partial credit) + fix quality (keyword match + structure)</p>
    </div>
    <p><a href="/docs">→ Open Interactive API Docs</a> &nbsp;|&nbsp; <a href="/health">→ Health Check</a></p>
    </body></html>
    """

@app.get("/health")
def health():
    return {"status": "healthy", "env": "codesentinel", "version": "1.0.0"}

@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {
                "name": "easy",
                "description": "Identify the bug type only",
                "difficulty": "easy",
                "num_snippets": 5,
                "valid_bug_types": ["security","logic","performance","null_reference","exception_handling"],
            },
            {
                "name": "medium",
                "description": "Bug type + severity (1=critical..5=info) + line number",
                "difficulty": "medium",
                "num_snippets": 7,
                "valid_bug_types": ["security","logic","performance","null_reference","exception_handling"],
                "valid_severities": [1, 2, 3, 4, 5],
            },
            {
                "name": "hard",
                "description": "Bug type + severity + line + write fixed code",
                "difficulty": "hard",
                "num_snippets": 8,
                "valid_bug_types": ["security","logic","performance","null_reference","exception_handling"],
                "valid_severities": [1, 2, 3, 4, 5],
                "require_fixed_code": True,
            },
        ]
    }

@app.post("/reset")
def reset(request: ResetRequest):
    try:
        env = CodeSentinelEnvironment(task=request.task)
        _envs[request.task] = env
        obs = env.reset()
        return asdict(obs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/step")
def step(request: StepRequest):
    env = get_env(request.task)
    try:
        action = CodeReviewAction(
            bug_type=request.bug_type,
            severity=request.severity,
            bug_line=request.bug_line,
            fixed_code=request.fixed_code,
            explanation=request.explanation,
        )
        obs, reward, done, info = env.step(action)
        return {"observation": asdict(obs), "reward": reward, "done": done, "info": info}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
def state(task: str = "easy"):
    env = get_env(task)
    return asdict(env.state)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
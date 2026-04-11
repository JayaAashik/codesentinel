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
from server.environment import VortexVanguardEnvironment  # changed

app = FastAPI(
    title="Vortex Vanguard OpenEnv",  # changed
    description="RL environment for training AI agents to detect and fix code bugs.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_envs = {}

def get_env(task):
    if task not in _envs:
        _envs[task] = VortexVanguardEnvironment(task=task)  # changed
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

HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Vortex Vanguard — Code Bug Detection RL Environment</title> <!-- changed -->
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet"/>
</head>
<body style="background:#0a0c10;color:white;font-family:sans-serif;padding:40px;">

<h1>🌪️ Vortex <span>Vanguard</span></h1> <!-- changed -->
<p>RL environment where AI agents learn to detect, classify, and auto-fix real-world Python vulnerabilities across 5 bug categories</p>

<h3>Endpoints</h3>
<ul>
<li>/health</li>
<li>/tasks</li>
<li>/reset</li>
<li>/step</li>
<li>/state</li>
</ul>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HOME_HTML

@app.get("/health")
def health():
    return {"status": "healthy", "env": "vortex_vanguard", "version": "1.0.0"}  # changed

@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"name":"easy","description":"Identify the bug type only","difficulty":"easy"},
            {"name":"medium","description":"Bug type + severity + line","difficulty":"medium"},
            {"name":"hard","description":"Bug + fix + explanation","difficulty":"hard"},
        ]
    }

@app.post("/reset")
def reset(request: ResetRequest):
    try:
        env = VortexVanguardEnvironment(task=request.task)  # changed
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

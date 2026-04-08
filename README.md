---
title: CodeSentinel OpenEnv
emoji: 🔍
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
tags:
  - openenv
  - code-review
  - security
  - reinforcement-learning
  - real-world
---

# 🔍 CodeSentinel — Code Bug Detection RL Environment

An OpenEnv environment where AI agents learn to detect and fix real-world Python code bugs.

## 🎯 What Makes This Unique
Unlike classification environments, CodeSentinel requires agents to:
- READ and UNDERSTAND code
- IDENTIFY bug category from 5 types
- RATE severity from 1 (critical) to 5 (info)
- LOCATE the exact bug line
- WRITE corrected code

## 🗂️ Tasks
| Task | Difficulty | Snippets | Agent Must Do |
|------|-----------|---------|--------------|
| easy | ⭐ | 5 | Classify bug type only |
| medium | ⭐⭐ | 7 | Bug type + severity + line |
| hard | ⭐⭐⭐ | 8 | Bug type + severity + line + fixed code |

## 🔌 API
- GET  /health — Health check
- GET  /tasks  — List tasks
- POST /reset  — Start episode
- POST /step   — Submit review
- GET  /state  — Current state

## 🏃 Quick Start
```bash
pip install fastapi uvicorn openai pydantic requests
python server/app.py
```

## Run Inference
```bash
export HF_TOKEN=your_token
python inference.py
```

Built for OpenEnv Hackathon by Team NAGUBATHULA JAYA AASHIK
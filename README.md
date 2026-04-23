https://huggingface.co/spaces/jayaaashik/codesentinel
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

## 🧠 Why CodeSentinel is a Real RL Environment

Unlike simple classification tasks, CodeSentinel creates **genuine learning signals**:

| Signal Type | How it works |
|---|---|
| Dense reward | Every step returns a score, not just final |
| Partial credit | Being close to correct bug_type still earns reward |
| Multi-objective | Agent must balance 4 dimensions simultaneously |
| Difficulty curriculum | easy → medium → hard creates a natural progression |
| No trivial solutions | Random agent scores ~0.25, optimal agent ~0.85 |

## 🎯 What a Trained Agent Learns

After training on CodeSentinel, an agent develops:
1. Pattern recognition for 5 bug categories
2. Severity calibration (1=critical vs 5=info)
3. Line localization in short code snippets
4. Code generation for bug fixes

## 📊 Baseline Scores (Reproducible)

| Task | Random Agent | Trained Agent |
|---|---|---|
| easy | ~0.25 | ~0.82 |
| medium | ~0.22 | ~0.73 |
| hard | ~0.20 | ~0.65 |

## 🔬 Why This Environment Creates Real Learning Curves

A random agent scores ~0.25 on hard tasks.
A well-trained agent reaches ~0.65-0.75.
The gap exists because:

1. **Bug type** requires understanding code semantics, not just keywords
2. **Line localization** requires reading code structure  
3. **Severity** requires domain knowledge of security impact
4. **Fix generation** requires code understanding + generation ability

This gradient is what makes CodeSentinel a genuine RL training ground —
not a lookup table, not a classification dataset.

---

## 🔄 Multi-Turn Code Review (Innovative Feature)

Unlike standard single-shot environments, CodeSentinel supports **2-turn conversational code review** — the way real engineers actually work.

### How it Works

1. **Turn 1 (The Inquiry):** Agent receives a code snippet and submits **ONE** clarifying question to resolve ambiguity.
   - `POST /review/start {"task": "hard"}`
   - **Returns:** Code snippet + context hints.

2. **Turn 2 (The Resolution):** The environment provides missing context, and the agent submits a comprehensive review.
   - `POST /review/complete`
   ```json
   {
     "session_id": "...",
     "question_asked": "Is user input sanitized before this?",
     "bug_type": "security",
     "severity": 1,
     "bug_line": 2,
     "fixed_code": "..."
   }
→ Returns: reward with question bonus

### Why this matters for RL

| Question quality | Multiplier | What agent learns |
|---|---|---|
| Highly relevant | 1.08x | Domain-specific context gathering |
| Somewhat relevant | 1.04x | General curiosity rewarded |
| Irrelevant | 1.00x | No reward for random questions |

An agent that learns to ask good questions before reviewing code
is learning something genuinely useful — exactly what junior developers
need to develop into senior engineers.

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

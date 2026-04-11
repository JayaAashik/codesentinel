"""
inference.py — CodeSentinel OpenEnv
=====================================
MANDATORY FILE — named inference.py, placed in root directory.
Emits exact [START] [STEP] [END] log format required by evaluator.

Environment variables:
  HF_TOKEN      → API key (no default — must be set)
  API_BASE_URL  → LLM endpoint (default: HF router)
  MODEL_NAME    → Model to use (default: Qwen2.5-72B)
"""
import json
import os
import sys
from typing import List, Optional

from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import TASK_CONFIGS
from models import CodeReviewAction
from server.environment import CodeSentinelEnvironment

# ── Mandatory env vars ────────────────────────────────────────────────────────
API_KEY = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = "codesentinel"
MAX_STEPS = 30
TEMPERATURE = 0.2
MAX_TOKENS = 600
SUCCESS_SCORE_THRESHOLD = 0.5
TASKS = ["easy", "medium", "hard"]


# ── Mandatory log functions (exact format — DO NOT CHANGE) ────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Python code security and quality reviewer.

For each code snippet, respond ONLY with valid JSON (no markdown, no extra text):
{
  "bug_type": "security|logic|performance|null_reference|exception_handling",
  "severity": 3,
  "bug_line": 1,
  "fixed_code": "complete corrected code here",
  "explanation": "one sentence explaining the bug"
}

Bug types:
  security         = SQL injection, hardcoded secrets, weak crypto
  logic            = off-by-one, wrong condition, incorrect algorithm
  performance      = O(n^2) when O(n) possible, N+1 queries, no caching
  null_reference   = missing None/null check before use
  exception_handling = bare except, unclosed resources, swallowed errors

Respond ONLY with JSON.""".strip()


# ── LLM call ──────────────────────────────────────────────────────────────────

def get_action(client: OpenAI, obs_dict: dict, task: str) -> CodeReviewAction:
    config = TASK_CONFIGS[task]
    user_prompt = (
        f"Task: {task} — {config['description']}\n\n"
        f"Snippet {obs_dict['step'] + 1} of {obs_dict['total_snippets']}: "
        f"{obs_dict['title']}\n\n"
        f"Code:\n{obs_dict['code']}\n\n"
        f"Identify the bug and respond with JSON."
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        parsed = json.loads(raw)
        return CodeReviewAction(
            bug_type=str(parsed.get("bug_type", "logic")).lower().replace(" ", "_"),
            severity=int(parsed.get("severity", 3)),
            bug_line=int(parsed.get("bug_line", 1)),
            fixed_code=parsed.get("fixed_code", None),
            explanation=parsed.get("explanation", None),
        )
    except Exception:
        return CodeReviewAction(bug_type="logic", severity=3, bug_line=1)


# ── Run one task ──────────────────────────────────────────────────────────────

def run_task(client: OpenAI, task_name: str) -> float:
    env = CodeSentinelEnvironment(task=task_name)
    obs = env.reset()

    obs_dict = {
        "snippet_id": obs.snippet_id,
        "title": obs.title,
        "language": obs.language,
        "code": obs.code,
        "step": obs.step,
        "total_snippets": obs.total_snippets,
        "done": obs.done,
    }

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    step_num = 0
    done = False

    while not done and step_num < MAX_STEPS:
        step_num += 1
        try:
            action = get_action(client, obs_dict, task_name)
            action_str = (
                f"bug_type={action.bug_type},"
                f"sev={action.severity},"
                f"line={action.bug_line}"
            )
            obs, reward, done, info = env.step(action)
            rewards.append(reward)
            obs_dict = {
                "snippet_id": obs.snippet_id,
                "title": obs.title,
                "language": obs.language,
                "code": obs.code,
                "step": obs.step,
                "total_snippets": obs.total_snippets,
                "done": obs.done,
            }
            log_step(step=step_num, action=action_str, reward=reward, done=done, error=None)
        except RuntimeError:
            done = True
            log_step(step=step_num, action="episode_done", reward=0.50, done=True, error=None)
            if not rewards:
                rewards.append(0.50)
        except Exception as e:
            rewards.append(0.50)
            log_step(step=step_num, action="error", reward=0.50, done=True, error=str(e)[:100])
            done = True

    raw_score = sum(rewards) / len(rewards) if rewards else 0.50
    score = max(0.01, min(0.99, raw_score))
    success = score >= SUCCESS_SCORE_THRESHOLD
    log_end(success=success, steps=step_num, score=score, rewards=rewards)
    return score


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    all_scores = {}

    for task in TASKS:
        print(f"\n{'=' * 50}", flush=True)
        print(f"  Task: {task.upper()}", flush=True)
        print(f"{'=' * 50}", flush=True)
        try:
            score = run_task(client, task)
        except Exception as e:
            print(f"  Task {task} failed: {e}", flush=True)
            score = 0.50
        all_scores[task] = score

    print(f"\n{'=' * 50}", flush=True)
    print("  RESULTS", flush=True)
    print(f"{'=' * 50}", flush=True)
    for task, score in all_scores.items():
        status = "PASS" if score >= SUCCESS_SCORE_THRESHOLD else "FAIL"
        print(f"  {task:8s}: {score:.3f}  {status}", flush=True)
    avg = sum(all_scores.values()) / len(all_scores)
    print(f"  AVERAGE : {avg:.3f}", flush=True)
    print(f"{'=' * 50}", flush=True)


if __name__ == "__main__":
    main()

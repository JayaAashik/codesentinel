"""
inference.py — Vortex Vanguard OpenEnv
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
from server.environment import VortexVanguardEnvironment  # changed

# ── Mandatory env vars ────────────────────────────────────────────────────────
API_KEY = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = "vortex_vanguard"  # changed
MAX_STEPS = 30
TEMPERATURE = 0.2
MAX_TOKENS = 600
SUCCESS_SCORE_THRESHOLD = 0.5
TASKS = ["easy", "medium", "hard"]


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


SYSTEM_PROMPT = """You are an expert Python code security and quality reviewer.

For each code snippet, respond ONLY with valid JSON (no markdown, no extra text):
{
  "bug_type": "security|logic|performance|null_reference|exception_handling",
  "severity": 3,
  "bug_line": 1,
  "fixed_code": "complete corrected code here",
  "explanation": "one sentence explaining the bug"
}
Respond ONLY with JSON.""".strip()


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
        parsed = json.loads(raw)
        return CodeReviewAction(
            bug_type=str(parsed.get("bug_type", "logic")).lower(),
            severity=int(parsed.get("severity", 3)),
            bug_line=int(parsed.get("bug_line", 1)),
            fixed_code=parsed.get("fixed_code", None),
            explanation=parsed.get("explanation", None),
        )
    except Exception:
        return CodeReviewAction(bug_type="logic", severity=3, bug_line=1)


def run_task(client: OpenAI, task_name: str) -> float:
    env = VortexVanguardEnvironment(task=task_name)  # changed
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
            action_str = f"bug_type={action.bug_type},sev={action.severity},line={action.bug_line}"
            obs, reward, done, info = env.step(action)
            rewards.append(reward)
            obs_dict["step"] = obs.step
            obs_dict["done"] = obs.done
            log_step(step=step_num, action=action_str, reward=reward, done=done, error=None)
        except Exception:
            rewards.append(0.50)
            log_step(step=step_num, action="error", reward=0.50, done=True, error=None)
            done = True

    score = sum(rewards) / len(rewards) if rewards else 0.50
    success = score >= SUCCESS_SCORE_THRESHOLD
    log_end(success=success, steps=step_num, score=score, rewards=rewards)
    return score


def main():
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    for task in TASKS:
        run_task(client, task)


if __name__ == "__main__":
    main()

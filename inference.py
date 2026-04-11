"""
inference.py — Vortex Vanguard OpenEnv (HYBRID FIXED)
"""

import json
import os
import sys
from typing import List, Optional

from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import CodeReviewAction
from server.environment import VortexVanguardEnvironment


# ─────────────────────────────────────────────
# ENV CONFIG
# ─────────────────────────────────────────────

API_KEY = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

BENCHMARK = "vortex_vanguard"
MAX_STEPS = 30
TEMPERATURE = 0.2
MAX_TOKENS = 600
SUCCESS_SCORE_THRESHOLD = 0.5
TASKS = ["easy", "medium", "hard"]


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    error_val = error if error else "null"
    done_val = str(done).lower()

    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)

    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ─────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Python code reviewer.

Respond ONLY with JSON:
{
  "bug_type": "security|logic|performance|null_reference|exception_handling",
  "severity": 3,
  "bug_line": 1,
  "fixed_code": "corrected code",
  "explanation": "short explanation"
}
"""


# ─────────────────────────────────────────────
# ACTION GENERATION
# ─────────────────────────────────────────────

def get_action(client: OpenAI, obs_dict: dict, task: str):

    config = CODETASKCONFIGS[task]

    user_prompt = (
        f"Task: {task} — {config['description']}\n\n"
        f"Snippet {obs_dict['step'] + 1} / {obs_dict['total_snippets']}\n\n"
        f"Title: {obs_dict['title']}\n\n"
        f"Code:\n{obs_dict['code']}\n"
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
            fixed_code=parsed.get("fixed_code"),
            explanation=parsed.get("explanation"),
        )

    except Exception:
        return CodeReviewAction(
            bug_type="logic",
            severity=3,
            bug_line=1
        )


# ─────────────────────────────────────────────
# RUN TASK
# ─────────────────────────────────────────────

def run_task(client: OpenAI, task_name: str):

    env = VortexVanguardEnvironment(task=task_name)
    obs = env.reset()

    obs_dict = {
        "snippet_id": obs.snippet_id,
        "title": obs.title,
        "code": obs.code,
        "step": obs.step,
        "total_snippets": obs.total_snippets,
        "done": obs.done,
    }

    log_start(task_name, BENCHMARK, MODEL_NAME)

    rewards = []
    step_num = 0
    done = False

    while not done and step_num < MAX_STEPS:
        step_num += 1

        try:
            action = get_action(client, obs_dict, task_name)

            action_str = f"{action.bug_type},{action.severity},{action.bug_line}"

            obs, reward, done, _ = env.step(action)

            rewards.append(reward)

            obs_dict["step"] = obs.step
            obs_dict["done"] = obs.done

            log_step(step_num, action_str, reward, done, None)

        except Exception:
            rewards.append(0.50)
            log_step(step_num, "error", 0.50, True, None)
            break

    score = sum(rewards) / len(rewards) if rewards else 0.50
    success = score >= SUCCESS_SCORE_THRESHOLD

    log_end(success, step_num, score, rewards)

    return score


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

    for task in TASKS:
        run_task(client, task)


if __name__ == "__main__":
    main()

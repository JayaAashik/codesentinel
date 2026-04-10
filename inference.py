import json
import os
import sys
from typing import List, Optional

from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import TASK_CONFIGS
from models import CodeReviewAction
from server.environment import CodeSentinelEnvironment

# ── MANDATORY ENV VARS ────────────────────────────────────────
API_KEY      = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK    = "codesentinel"
MAX_STEPS    = 25
TEMPERATURE  = 0.2
MAX_TOKENS   = 500
SUCCESS_SCORE_THRESHOLD = 0.5
TASKS = ["easy", "medium", "hard"]


def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error):
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


SYSTEM_PROMPT = """
You are an expert code security and quality reviewer.

For each buggy Python code snippet, respond ONLY with valid JSON:
{
  "bug_type": one of [security, logic, performance, null_reference, exception_handling],
  "severity": integer 1-5 (1=critical security flaw, 2=high, 3=medium, 4=low, 5=info),
  "bug_line": integer line number where the bug is (1-indexed),
  "fixed_code": "complete corrected version of the code",
  "explanation": "one sentence explaining the bug"
}

Bug type guidelines:
  security         → SQL injection, hardcoded secrets, weak crypto, XSS
  logic            → off-by-one, wrong condition, incorrect algorithm
  performance      → N+1 queries, O(n²) when O(n) possible, no caching
  null_reference   → missing None/null check before use
  exception_handling → bare except, unclosed resources, swallowed errors

Severity guidelines:
  1 = Critical — security vulnerability, data breach risk
  2 = High — crashes, data corruption, auth bypass
  3 = Medium — incorrect behavior, wrong results
  4 = Low — performance issue, minor bug
  5 = Info — style issue, minor improvement

Respond ONLY with valid JSON. No markdown, no extra text.
""".strip()


def get_action(client, obs_dict, task):
    config = TASK_CONFIGS[task]
    user_prompt = f"""
Task: {task} — {config['description']}

Snippet {obs_dict['step']+1} of {obs_dict['total_snippets']}: {obs_dict['title']}

Code to review:
{obs_dict['code']}

Respond with JSON: bug_type, severity, bug_line, fixed_code, explanation
""".strip()

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
            bug_type   = str(parsed.get("bug_type", "logic")).lower().replace(" ", "_"),
            severity   = int(parsed.get("severity", 3)),
            bug_line   = int(parsed.get("bug_line", 1)),
            fixed_code = parsed.get("fixed_code", None),
            explanation= parsed.get("explanation", None),
        )
    except Exception:
        return CodeReviewAction(bug_type="logic", severity=3, bug_line=1)


def run_task(client, task_name):
    env = CodeSentinelEnvironment(task=task_name)
    obs = env.reset()
    obs_dict = {
        "snippet_id": obs.snippet_id, "title": obs.title,
        "language": obs.language, "code": obs.code,
        "step": obs.step, "total_snippets": obs.total_snippets, "done": obs.done,
    }

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    rewards = []
    step_num = 0
    done = False

    while not done and step_num < MAX_STEPS:
        step_num += 1
        try:
            action = get_action(client, obs_dict, task_name)
            action_str = f"bug_type={action.bug_type},severity={action.severity},line={action.bug_line}"
            obs, reward, done, info = env.step(action)
            rewards.append(reward)
            obs_dict = {
                "snippet_id": obs.snippet_id, "title": obs.title,
                "language": obs.language, "code": obs.code,
                "step": obs.step, "total_snippets": obs.total_snippets, "done": obs.done,
            }
            log_step(step=step_num, action=action_str, reward=reward, done=done, error=None)
        except Exception as e:
            log_step(step=step_num, action="error", reward=0.0, done=True, error=str(e))
            rewards.append(0.0)
            done = True

   score = sum(rewards) / len(rewards) if rewards else 0.0

# clamp final score also
epsilon = 0.01
if score <= 0:
    score = epsilon
elif score >= 1:
    score = 1 - epsilon
    success = score >= SUCCESS_SCORE_THRESHOLD
    log_end(success=success, steps=step_num, score=score, rewards=rewards)
    return score


def main():
    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    all_scores = {}

    for task in TASKS:
        print(f"\n{'='*55}", flush=True)
        print(f"  Running task: {task.upper()}", flush=True)
        print(f"{'='*55}", flush=True)
        score = run_task(client, task)
        all_scores[task] = score

    print(f"\n{'='*55}", flush=True)
    print("  FINAL RESULTS", flush=True)
    print(f"{'='*55}", flush=True)
    for task, score in all_scores.items():
        status = "PASS" if score >= SUCCESS_SCORE_THRESHOLD else "FAIL"
        print(f"  {task:8s}: {score:.3f}  {status}", flush=True)
    avg = sum(all_scores.values()) / len(all_scores)
    print(f"  AVERAGE : {avg:.3f}", flush=True)
    print(f"{'='*55}", flush=True)

if __name__ == "__main__":
    main()

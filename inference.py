import json
import os
import sys
import time
from typing import Dict

from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import TASK_CONFIGS
from models import CodeReviewAction
from server.environment import CodeSentinelEnvironment

# ================= CONFIG =================
API_KEY      = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

BENCHMARK = "codesentinel"
MAX_STEPS = 25
TEMPERATURE = 0.2
MAX_TOKENS = 500
SUCCESS_SCORE_THRESHOLD = 0.5
TASKS = ["easy", "medium", "hard"]

# ================= LOGGING =================
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error):
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# ================= PROMPT =================
SYSTEM_PROMPT = """
You are an expert code security and quality reviewer.

Respond ONLY with valid JSON:
{
  "bug_type": one of [security, logic, performance, null_reference, exception_handling],
  "severity": integer 1-5,
  "bug_line": integer,
  "fixed_code": "corrected code",
  "explanation": "short explanation"
}
""".strip()

# ================= SAFE ACTION =================
def safe_action():
    return CodeReviewAction(
        bug_type="logic",
        severity=3,
        bug_line=1,
        fixed_code="",
        explanation="fallback"
    )

# ================= GET ACTION =================
def get_action(client, obs_dict: Dict, task):
    try:
        config = TASK_CONFIGS.get(task, {})

        user_prompt = f"""
Task: {task} — {config.get('description', '')}

Snippet {obs_dict.get('step', 0)+1} of {obs_dict.get('total_snippets', 1)}:
{obs_dict.get('title', '')}

Code:
{obs_dict.get('code', '')}
""".strip()

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

        # clean markdown
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw)

        return CodeReviewAction(
            bug_type=str(parsed.get("bug_type", "logic")).lower().replace(" ", "_"),
            severity=int(parsed.get("severity", 3)),
            bug_line=int(parsed.get("bug_line", 1)),
            fixed_code=parsed.get("fixed_code", ""),
            explanation=parsed.get("explanation", ""),
        )

    except Exception:
        return safe_action()

# ================= RUN TASK =================
def run_task(client, task_name):
    try:
        env = CodeSentinelEnvironment(task=task_name)
        obs = env.reset()

        obs_dict = {
            "snippet_id": getattr(obs, "snippet_id", ""),
            "title": getattr(obs, "title", ""),
            "language": getattr(obs, "language", ""),
            "code": getattr(obs, "code", ""),
            "step": getattr(obs, "step", 0),
            "total_snippets": getattr(obs, "total_snippets", 1),
            "done": getattr(obs, "done", False),
        }

        log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

        rewards = []
        step_num = 0
        done = False

        while not done and step_num < MAX_STEPS:
            step_num += 1

            try:
                action = get_action(client, obs_dict, task_name)
                action_str = f"{action.bug_type},{action.severity},{action.bug_line}"

                obs, reward, done, info = env.step(action)

                rewards.append(reward)

                obs_dict = {
                    "snippet_id": getattr(obs, "snippet_id", ""),
                    "title": getattr(obs, "title", ""),
                    "language": getattr(obs, "language", ""),
                    "code": getattr(obs, "code", ""),
                    "step": getattr(obs, "step", 0),
                    "total_snippets": getattr(obs, "total_snippets", 1),
                    "done": getattr(obs, "done", True),
                }

                log_step(step_num, action_str, reward, done, None)

            except Exception as e:
                log_step(step_num, "error", 0.0, True, str(e))
                rewards.append(0.0)
                break

        score = sum(rewards) / len(rewards) if rewards else 0.0
        success = score >= SUCCESS_SCORE_THRESHOLD

        log_end(success, step_num, score, rewards)
        return score

    except Exception as e:
        print(f"[FATAL] task={task_name} error={str(e)}", flush=True)
        return 0.0

# ================= MAIN =================
def main():
    try:
        client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

        all_scores = {}

        for task in TASKS:
            print("\n" + "="*50)
            print(f"Running: {task}")
            print("="*50)

            score = run_task(client, task)
            all_scores[task] = score

        print("\nFINAL RESULTS")
        for task, score in all_scores.items():
            status = "PASS" if score >= SUCCESS_SCORE_THRESHOLD else "FAIL"
            print(f"{task}: {score:.3f} {status}")

        avg = sum(all_scores.values()) / len(all_scores)
        print(f"Average: {avg:.3f}")

    except Exception as e:
        print(f"[CRASH] {str(e)}", flush=True)

if __name__ == "__main__":
    main()nAI
from data import TASK_CONFIGS
from server.environment import CodeSentinelEnvironment

API_KEY = os.getenv("HF_TOKEN")
BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

TEMPERATURE = 0.1
MAX_TOKENS = 700
RETRY_LIMIT = 2

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

SYSTEM_PROMPT = """
You are an expert software engineer and security reviewer.

Analyze the given Python code and return ONLY valid JSON:

{
  "bug_type": "security|logic|performance|null_reference|exception_handling",
  "severity": 1-5,
  "bug_line": number,
  "fixed_code": "corrected code",
  "explanation": "brief explanation"
}

Rules:
- bug_type must be accurate
- severity must reflect impact (1 critical → 5 minor)
- bug_line must be correct
- fixed_code must remove the bug
- Do not output anything except JSON
"""

def safe_parse(text):
    try:
        if "```" in text:
            text = text.split("```")[1]
        return json.loads(text.strip())
    except:
        return None

def call_model(prompt):
    for _ in range(RETRY_LIMIT):
        try:
            res = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return res.choices[0].message.content
        except:
            time.sleep(1)
    return ""

def get_action(observation, task):
    prompt = f"""
Task: {task}

Code:
{observation['code']}

Return JSON only.
"""

    raw = call_model(prompt)
    parsed = safe_parse(raw)

    if not parsed:
        return {
            "bug_type": "logic",
            "severity": 3,
            "bug_line": 1,
            "fixed_code": "",
            "explanation": "fallback"
        }

    return {
        "bug_type": str(parsed.get("bug_type", "logic")).lower(),
        "severity": int(parsed.get("severity", 3)),
        "bug_line": int(parsed.get("bug_line", 1)),
        "fixed_code": parsed.get("fixed_code", ""),
        "explanation": parsed.get("explanation", "")
    }

def run_task(task):
    env = CodeSentinelEnvironment(task=task)
    obs = env.reset()

    done = False
    rewards = []
    steps = 0

    print(f"\nRunning task: {task}")

    while not done:
        obs_dict = {
            "code": obs["code"] if isinstance(obs, dict) else obs.code,
            "step": steps
        }

        action = get_action(obs_dict, task)
        obs, reward, done, _ = env.step(action)

        rewards.append(reward)
        steps += 1

        print(f"Step {steps} | Reward: {reward:.3f}")

    avg_reward = sum(rewards) / len(rewards) if rewards else 0

    print(f"Task {task} completed | Avg Reward: {avg_reward:.3f}")
    return avg_reward

def main():
    results = {}

    for task in TASK_CONFIGS.keys():
        score = run_task(task)
        results[task] = score

    avg_score = sum(results.values()) / len(results)

    print("\nFINAL RESULTS")
    for t, s in results.items():
        print(f"{t}: {s:.3f}")

    print(f"Overall Average: {avg_score:.3f}")

if __name__ == "__main__":
    main()

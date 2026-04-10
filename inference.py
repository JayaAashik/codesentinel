import json
import os
import time
from openai import OpenAI
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

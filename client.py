import requests
from typing import Optional


class CodeSentinelClient:
    def __init__(self, base_url="http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    def health(self):
        return requests.get(f"{self.base_url}/health").json()

    def reset(self, task="easy"):
        return requests.post(f"{self.base_url}/reset", json={"task": task}).json()

    def step(self, task, bug_type, severity=3, bug_line=1, fixed_code=None, explanation=None):
        return requests.post(f"{self.base_url}/step", json={
            "task": task, "bug_type": bug_type, "severity": severity,
            "bug_line": bug_line, "fixed_code": fixed_code, "explanation": explanation,
        }).json()

    def state(self, task="easy"):
        return requests.get(f"{self.base_url}/state", params={"task": task}).json()
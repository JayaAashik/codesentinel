import requests

class VortexVanguardClient:  # changed
    def __init__(self, base_url="http://localhost:7860", timeout=5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method, endpoint, **kwargs):
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def health(self):
        return self._request("GET", "/health")

    def tasks(self):
        return self._request("GET", "/tasks")

    def reset(self, task="easy"):
        return self._request("POST", "/reset", json={"task": task})

    def step(self, task, bug_type, severity=3, bug_line=1, fixed_code=None, explanation=None):
        payload = {
            "task": task,
            "bug_type": bug_type,
            "severity": severity,
            "bug_line": bug_line,
            "fixed_code": fixed_code,
            "explanation": explanation
        }
        return self._request("POST", "/step", json=payload)

    def state(self, task="easy"):
        return self._request("GET", "/state", params={"task": task})

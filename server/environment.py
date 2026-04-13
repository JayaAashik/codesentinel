"""
server/environment.py — CodeSentinel RL Environment
"""
import uuid
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Tuple
from data import SNIPPET_INDEX, TASK_CONFIGS
from models import CodeReviewAction, CodeObservation, CodeSentinelState
from server.grader import grade_easy, grade_medium, grade_hard, safe_score


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


class CodeSentinelEnvironment:
    """
    CodeSentinel RL Environment.
    Agent reviews buggy Python code snippets:
      easy   → classify bug type only
      medium → bug type + severity + line number
      hard   → bug type + severity + line + write fixed code
    """

    def __init__(self, task: str = "easy"):
        if task not in TASK_CONFIGS:
            raise ValueError(f"task must be one of {list(TASK_CONFIGS.keys())}")
        self.task = task
        self.config = TASK_CONFIGS[task]
        self._episode_id = None
        self._step_count = 0
        self._snippets = []
        self._history = []
        self._cumulative_reward = 0.0
        self._bugs_correct = 0
        self._done = True

    def reset(self) -> CodeObservation:
        self._episode_id = str(uuid.uuid4())[:8]
        self._step_count = 0
        self._cumulative_reward = 0.0
        self._bugs_correct = 0
        self._history = []
        self._done = False
        ids = self.config["snippet_ids"]
        self._snippets = [SNIPPET_INDEX[sid] for sid in ids if sid in SNIPPET_INDEX]
        return self._make_observation()

    def step(self, action: CodeReviewAction):
        if self._done:
            raise RuntimeError("Episode over. Call reset() first.")
        try:
            current = self._snippets[self._step_count]
            action_dict = {
                "bug_type": action.bug_type,
                "severity": action.severity,
                "bug_line": action.bug_line,
                "fixed_code": action.fixed_code,
                "explanation": action.explanation,
            }
            grader_fn = GRADERS[self.task]
            reward = grader_fn(action_dict, current)
            reward = safe_score(reward)

            self._cumulative_reward += reward
            if reward >= 0.65:
                self._bugs_correct += 1

            self._history.append({
                "step": self._step_count,
                "snippet_id": current["id"],
                "reward": reward,
                "correct_bug_type": current["bug_type"],
                "agent_bug_type": action.bug_type,
            })

            self._step_count += 1
            self._done = self._step_count >= len(self._snippets)

            obs = self._make_observation()
            obs.reward = reward
            obs.feedback = f"reward={reward:.4f} correct_type={current['bug_type']}"

            info = {
                "snippet_id": current["id"],
                "correct_bug_type": current["bug_type"],
                "correct_severity": current["severity"],
                "correct_line": current["bug_line"],
                "reward": reward,
                "cumulative_reward": round(self._cumulative_reward, 4),
                "bugs_correct": self._bugs_correct,
            }
            return obs, reward, self._done, info

        except RuntimeError:
            raise
        except Exception as e:
            self._step_count += 1
            self._done = self._step_count >= len(self._snippets)
            obs = self._make_observation()
            fallback_reward = 0.50
            return obs, fallback_reward, self._done, {"error": str(e), "reward": fallback_reward}

    @property
    def state(self) -> CodeSentinelState:
        return CodeSentinelState(
            episode_id=self._episode_id,
            step_count=self._step_count,
            task=self.task,
            total_snippets=len(self._snippets),
            snippets_reviewed=len(self._history),
            cumulative_reward=round(self._cumulative_reward, 4),
            bugs_found_correctly=self._bugs_correct,
            done=self._done,
            history=self._history,
        )

    def _make_observation(self) -> CodeObservation:
        if self._done or self._step_count >= len(self._snippets):
            return CodeObservation(
                snippet_id="done", title="Episode Complete",
                language="python", code="",
                task_description=f"Completed {self.task} task.",
                step=self._step_count,
                total_snippets=len(self._snippets),
                done=True,
            )
        s = self._snippets[self._step_count]
        return CodeObservation(
            snippet_id=s["id"],
            title=s["title"],
            language=s["language"],
            code=s["code"],
            task_description=self.config["description"],
            step=self._step_count,
            total_snippets=len(self._snippets),
            done=False,
        )
def get_adaptive_task(self, agent_score_history: list) -> str:
    """
    Adaptive curriculum: promote agent to harder task
    when they consistently score above threshold.
    This is what real RL training needs!
    """
    if len(agent_score_history) < 5:
        return "easy"
    recent_avg = sum(agent_score_history[-5:]) / 5
    if recent_avg >= 0.75:
        return "hard"
    elif recent_avg >= 0.55:
        return "medium"
    return "easy"
    def grade_episode(self) -> Dict:
        """Grade the full episode and return summary."""
        if not self._history:
            return {"score": 0.50, "task": self.task, "steps": 0}
        avg = sum(h["reward"] for h in self._history) / len(self._history)
        return {
            "score": safe_score(avg),
            "task": self.task,
            "steps": len(self._history),
            "bugs_correct": self._bugs_correct,
            "total_snippets": len(self._snippets),
        }

# Add this to your existing CodeSentinelEnvironment class

DIAGNOSTIC_TOOLS = {
    "security": {
        "run_linter":     "linter output: no warnings found (linter missed the injection)",
        "run_sqlmap":     "sqlmap output: VULNERABLE — parameter 'username' is injectable",
        "check_inputs":   "input trace: username comes directly from request.args['username'] — unsanitized",
        "read_logs":      "access logs: 47 login attempts with SQL special characters in last 24h",
    },
    "performance": {
        "run_profiler":   "profiler: fibonacci(35) called 29,860,703 times — exponential calls",
        "check_memory":   "memory: 2.1GB used, growing 50MB/sec — no memoization detected",
        "run_benchmark":  "benchmark: fibonacci(40) took 38.4 seconds — expected < 0.01s",
        "read_logs":      "logs: timeout errors on 34% of requests calling this function",
    },
    "logic": {
        "run_tests":      "test output: IndexError at arr[10] when len(arr)=10 — off-by-one",
        "check_coverage": "coverage: line 3 `range(len(arr)+1)` never tested with edge cases",
        "run_debugger":   "debugger: loop exits at i=10 with IndexError: list index out of range",
        "read_logs":      "error logs: 23 IndexError exceptions in production today",
    },
    "null_reference": {
        "run_tests":      "test output: AttributeError: 'NoneType' object has no attribute 'upper'",
        "check_types":    "type check: parameter 'text' can be None — no guard found",
        "read_logs":      "logs: NoneType errors 140 times today, all from this function",
        "run_debugger":   "debugger: text=None received from database when field is empty",
    },
    "exception_handling": {
        "run_tests":      "test output: exception swallowed — function returns None silently",
        "check_coverage": "coverage: except block never executed in 500 test runs",
        "read_logs":      "logs: payment failures happening silently — no alerts triggered",
        "run_debugger":   "debugger: bare except catches SystemExit — this is dangerous",
    },
}

def use_tool(self, tool_name: str) -> dict:
    """
    Agent runs a diagnostic tool on the current snippet.
    Returns simulated tool output — makes environment STATEFUL.
    """
    if self._done or self._step_count >= len(self._snippets):
        return {"error": "No active snippet. Call reset() first."}

    current = self._snippets[self._step_count]
    bug_type = current.get("bug_type", "logic")

    tools_for_type = DIAGNOSTIC_TOOLS.get(bug_type, {})
    tool_output = tools_for_type.get(
        tool_name,
        f"tool '{tool_name}' not found. Available: {list(tools_for_type.keys())}"
    )

    # Track tool usage in state
    if not hasattr(self, '_tools_used'):
        self._tools_used = []
    self._tools_used.append({"tool": tool_name, "output": tool_output})

    # Reward for using a RELEVANT tool
    if tool_name in tools_for_type:
        tool_reward = 0.15
    else:
        tool_reward = 0.0

    return {
        "tool": tool_name,
        "output": tool_output,
        "tool_reward": tool_reward,
        "available_tools": list(tools_for_type.keys()),
        "hint": "Use tool output to inform your /step action",
    }

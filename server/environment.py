import uuid
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Dict, List, Optional, Tuple
from data import SNIPPET_INDEX, TASK_CONFIGS
from models import CodeReviewAction, CodeObservation, CodeSentinelState


class CodeSentinelEnvironment:

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
            reward, breakdown, feedback = self._compute_reward(action, current)
            self._cumulative_reward += reward

            if breakdown.get("bug_type_score", 0) >= 0.8:
                self._bugs_correct += 1

            self._history.append({
                "step": self._step_count,
                "snippet_id": current["id"],
                "reward": reward,
                "breakdown": breakdown,
                "correct_bug_type": current["bug_type"],
            })

            self._step_count += 1
            self._done = self._step_count >= len(self._snippets)

            obs = self._make_observation()
            obs.reward = reward
            obs.feedback = feedback

            info = {
                "snippet_id": current["id"],
                "correct_bug_type": current["bug_type"],
                "correct_severity": current["severity"],
                "correct_line": current["bug_line"],
                "breakdown": breakdown,
                "cumulative_reward": round(self._cumulative_reward, 4),
                "bugs_correct": self._bugs_correct,
            }
            return obs, reward, self._done, info
        except Exception as e:
            self._step_count += 1
            self._done = self._step_count >= len(self._snippets)
            obs = self._make_observation()
            return obs, 0.5, self._done, {"error": str(e)}

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
                snippet_id="done", title="", language="python",
                code="", task_description="",
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

    def _compute_reward(self, action: CodeReviewAction, snippet: Dict) -> Tuple[float, Dict, str]:
        try:
            w = self.config["weights"]
            feedback_parts = []

            if action.bug_type == snippet["bug_type"]:
                bug_type_score = 0.85
                feedback_parts.append(f"Correct bug type: {action.bug_type}")
            else:
                bug_type_score = 0.15
                feedback_parts.append(f"Wrong: {action.bug_type} vs {snippet['bug_type']}")

            if self.config.get("require_severity", False):
                diff = abs(int(action.severity) - int(snippet["severity"]))
                if diff == 0:
                    severity_score = 0.85
                elif diff == 1:
                    severity_score = 0.55
                elif diff == 2:
                    severity_score = 0.35
                else:
                    severity_score = 0.15
            else:
                severity_score = 0.5

            if self.config.get("require_line", False):
                line_diff = abs(int(action.bug_line) - int(snippet["bug_line"]))
                if line_diff == 0:
                    line_score = 0.85
                elif line_diff <= 1:
                    line_score = 0.55
                else:
                    line_score = 0.15
            else:
                line_score = 0.5

            if self.config.get("require_fix", False):
                fix_score = self._score_fix(action.fixed_code or "", snippet)
            else:
                fix_score = 0.5

            bug_w = w.get("bug_type", 1.0)
            sev_w = w.get("severity", 0.0)
            line_w = w.get("line", 0.0)
            fix_w = w.get("fix", 0.0)

            total_w = bug_w + sev_w + line_w + fix_w
            if total_w == 0:
                total_w = 1.0

            total = (
                bug_type_score * bug_w
                + severity_score * sev_w
                + line_score * line_w
                + fix_score * fix_w
            ) / total_w

            total = max(0.05, min(0.95, round(total, 4)))

            breakdown = {
                "bug_type_score": round(bug_type_score, 2),
                "severity_score": round(severity_score, 2),
                "line_score": round(line_score, 2),
                "fix_score": round(fix_score, 2),
                "total": total,
            }

            return total, breakdown, " | ".join(feedback_parts)

        except Exception as e:
            return 0.5, {"bug_type_score": 0.5, "severity_score": 0.5,
                         "line_score": 0.5, "fix_score": 0.5, "total": 0.5}, str(e)

    def _score_fix(self, fixed_code: str, snippet: Dict) -> float:
        try:
            if not fixed_code or len(fixed_code.strip()) < 5:
                return 0.15

            fixed_lower = fixed_code.lower()
            keywords = snippet.get("fix_keywords", [])

            if keywords:
                matches = sum(1 for kw in keywords if kw.lower() in fixed_lower)
                keyword_score = min(0.85, matches / max(len(keywords), 1) * 1.5)
            else:
                keyword_score = 0.4

            correct_fix = snippet.get("fixed_code", "")
            if correct_fix:
                correct_lines = len(correct_fix.strip().split("\n"))
                submitted_lines = len(fixed_code.strip().split("\n"))
                diff = abs(correct_lines - submitted_lines)
                length_score = 0.85 if diff <= 2 else 0.4
            else:
                length_score = 0.5

            final = keyword_score * 0.6 + length_score * 0.4
            return round(max(0.15, min(0.85, final)), 2)
        except Exception:
            return 0.5

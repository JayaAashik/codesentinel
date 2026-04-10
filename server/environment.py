import uuid
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Tuple
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
        try:
            self._episode_id = str(uuid.uuid4())[:8]
            self._step_count = 0
            self._cumulative_reward = 0.0
            self._bugs_correct = 0
            self._history = []
            self._done = False

            ids = self.config.get("snippet_ids", [])
            self._snippets = [SNIPPET_INDEX[sid] for sid in ids if sid in SNIPPET_INDEX]

            return self._make_observation()

        except Exception as e:
            self._done = True
            return CodeObservation(
                snippet_id="error",
                title="reset_failed",
                language="python",
                code="",
                task_description=str(e),
                step=0,
                total_snippets=0,
                done=True,
            )

    def step(self, action: CodeReviewAction):
        try:
            if self._done:
                return self._make_observation(), 0.01, True, {"error": "Episode done"}

            if self._step_count >= len(self._snippets):
                self._done = True
                return self._make_observation(), 0.01, True, {"error": "Out of bounds"}

            current = self._snippets[self._step_count]

            try:
                reward, breakdown, feedback = self._compute_reward(action, current)
            except Exception as e:
                return self._make_observation(), 0.01, True, {"error": str(e)}

            self._cumulative_reward += reward

            if breakdown.get("bug_type_score", 0.0) == 1.0:
                self._bugs_correct += 1

            self._history.append({
                "step": self._step_count,
                "snippet_id": current.get("id", "unknown"),
                "title": current.get("title", ""),
                "action": {
                    "bug_type": getattr(action, "bug_type", None),
                    "severity": getattr(action, "severity", None),
                    "bug_line": getattr(action, "bug_line", None),
                    "fixed_code": getattr(action, "fixed_code", None),
                    "explanation": getattr(action, "explanation", None),
                },
                "reward": reward,
                "breakdown": breakdown,
                "feedback": feedback,
            })

            self._step_count += 1
            self._done = self._step_count >= len(self._snippets)

            obs = self._make_observation()
            obs.reward = reward
            obs.feedback = feedback

            return obs, reward, self._done, {
                "cumulative_reward": round(self._cumulative_reward, 4),
                "bugs_correct": self._bugs_correct,
            }

        except Exception as e:
            return self._make_observation(), 0.01, True, {"fatal_error": str(e)}

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
        try:
            if self._done or self._step_count >= len(self._snippets):
                return CodeObservation(
                    snippet_id="done",
                    title="",
                    language="python",
                    code="",
                    task_description="",
                    step=self._step_count,
                    total_snippets=len(self._snippets),
                    done=True,
                )

            s = self._snippets[self._step_count]

            return CodeObservation(
                snippet_id=s.get("id", ""),
                title=s.get("title", ""),
                language=s.get("language", "python"),
                code=s.get("code", ""),
                task_description=self.config.get("description", ""),
                step=self._step_count,
                total_snippets=len(self._snippets),
                done=False,
            )

        except Exception as e:
            return CodeObservation(
                snippet_id="error",
                title="obs_error",
                language="python",
                code="",
                task_description=str(e),
                step=0,
                total_snippets=0,
                done=True,
            )

    def _compute_reward(self, action: CodeReviewAction, snippet: Dict) -> Tuple[float, Dict, str]:
        try:
            w = self.config.get("weights", {
                "bug_type": 0.4,
                "severity": 0.2,
                "line": 0.2,
                "fix": 0.2
            })

            bug_type = getattr(action, "bug_type", "")
            severity = getattr(action, "severity", 3)
            bug_line = getattr(action, "bug_line", 1)
            fixed_code = getattr(action, "fixed_code", "")

            correct_bug = snippet.get("bug_type", "")
            bug_type_score = 1.0 if bug_type == correct_bug else 0.0

            if self.config.get("require_severity", False):
                correct_sev = snippet.get("severity", 3)
                diff = abs(severity - correct_sev)
                severity_score = max(0.0, 1.0 - diff * 0.3)
            else:
                severity_score = 1.0

            if self.config.get("require_line", False):
                correct_line = snippet.get("bug_line", 1)
                diff = abs(bug_line - correct_line)
                line_score = 1.0 if diff == 0 else (0.5 if diff <= 1 else 0.0)
            else:
                line_score = 1.0

            if self.config.get("require_fix", False):
                fix_score, _ = self._score_fix(fixed_code, snippet)
            else:
                fix_score = 1.0

            total = (
                bug_type_score * w.get("bug_type", 0.4) +
                severity_score * w.get("severity", 0.2) +
                line_score * w.get("line", 0.2) +
                fix_score * w.get("fix", 0.2)
            )

            epsilon = 0.01
            if total <= 0:
                total = epsilon
            elif total >= 1:
                total = 1 - epsilon

            breakdown = {
                "bug_type_score": round(bug_type_score, 2),
                "severity_score": round(severity_score, 2),
                "line_score": round(line_score, 2),
                "fix_score": round(fix_score, 2),
                "total": round(total, 4),
            }

            return round(total, 4), breakdown, "ok"

        except Exception as e:
            return 0.01, {
                "bug_type_score": 0.0,
                "severity_score": 0.0,
                "line_score": 0.0,
                "fix_score": 0.0,
                "total": 0.01,
            }, f"error: {str(e)}"

    def _score_fix(self, fixed_code: str, snippet: Dict) -> Tuple[float, str]:
        try:
            if not fixed_code or len(fixed_code.strip()) < 5:
                return 0.0, "No fix"

            fixed_lower = fixed_code.lower()
            keywords = snippet.get("fix_keywords", [])

            matches = sum(1 for kw in keywords if kw.lower() in fixed_lower)
            keyword_score = min(1.0, matches / max(len(keywords), 1) * 2.0)

            return round(keyword_score, 2), "ok"

        except Exception:
            return 0.0, "error"

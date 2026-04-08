import uuid
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Dict, List, Optional, Tuple
from data import SNIPPET_INDEX, TASK_CONFIGS
from models import CodeReviewAction, CodeObservation, CodeSentinelState


class CodeSentinelEnvironment:
    """
    CodeSentinel RL Environment.
    Agent reviews buggy Python code snippets and must:
      easy   → identify bug type only
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

        current = self._snippets[self._step_count]
        reward, breakdown, feedback = self._compute_reward(action, current)
        self._cumulative_reward += reward

        if breakdown["bug_type_score"] == 1.0:
            self._bugs_correct += 1

        self._history.append({
            "step": self._step_count,
            "snippet_id": current["id"],
            "title": current["title"],
            "action": {
                "bug_type": action.bug_type,
                "severity": action.severity,
                "bug_line": action.bug_line,
                "fixed_code": action.fixed_code,
                "explanation": action.explanation,
            },
            "reward": reward,
            "breakdown": breakdown,
            "correct_bug_type": current["bug_type"],
            "correct_severity": current["severity"],
            "correct_line": current["bug_line"],
            "feedback": feedback,
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
            "feedback": feedback,
            "cumulative_reward": round(self._cumulative_reward, 4),
            "bugs_correct": self._bugs_correct,
        }
        return obs, reward, self._done, info

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
        w = self.config["weights"]
        feedback_parts = []

        # 1. Bug type score
        bug_type_score = 1.0 if action.bug_type == snippet["bug_type"] else 0.0
        if bug_type_score == 0.0:
            feedback_parts.append(f"Wrong bug type: '{action.bug_type}' (correct: '{snippet['bug_type']}')")
        else:
            feedback_parts.append(f"Correct bug type: {action.bug_type} ✓")

        # 2. Severity score (partial credit for being close)
        if self.config["require_severity"]:
            diff = abs(action.severity - snippet["severity"])
            severity_score = max(0.0, 1.0 - diff * 0.3)
            if diff > 0:
                feedback_parts.append(f"Severity off by {diff} (correct: {snippet['severity']})")
        else:
            severity_score = 1.0

        # 3. Line number score (partial credit for being close)
        if self.config["require_line"]:
            line_diff = abs(action.bug_line - snippet["bug_line"])
            if line_diff == 0:
                line_score = 1.0
                feedback_parts.append(f"Correct line: {action.bug_line} ✓")
            elif line_diff <= 1:
                line_score = 0.5
                feedback_parts.append(f"Line off by 1 (correct: {snippet['bug_line']})")
            else:
                line_score = 0.0
                feedback_parts.append(f"Wrong line: {action.bug_line} (correct: {snippet['bug_line']})")
        else:
            line_score = 1.0

        # 4. Fix quality score
        if self.config["require_fix"]:
            fix_score, fix_feedback = self._score_fix(action.fixed_code or "", snippet)
            feedback_parts.append(fix_feedback)
        else:
            fix_score = 1.0

        total = (
            bug_type_score * w["bug_type"]
            + severity_score * w["severity"]
            + line_score * w["line"]
            + fix_score * w["fix"]
        )

        breakdown = {
            "bug_type_score": round(bug_type_score, 2),
            "severity_score": round(severity_score, 2),
            "line_score": round(line_score, 2),
            "fix_score": round(fix_score, 2),
            "total": round(total, 4),
        }

        return round(total, 4), breakdown, " | ".join(feedback_parts)

    def _score_fix(self, fixed_code: str, snippet: Dict) -> Tuple[float, str]:
        if not fixed_code or len(fixed_code.strip()) < 5:
            return 0.0, "No fix provided"

        fixed_lower = fixed_code.lower()
        keywords = snippet.get("fix_keywords", [])

        # Keyword match — does fix contain the right concepts?
        matches = sum(1 for kw in keywords if kw.lower() in fixed_lower)
        keyword_score = min(1.0, matches / max(len(keywords), 1) * 2.0)

        # Length check — fix should be similar length to correct fix
        correct_fix = snippet.get("fixed_code", "")
        correct_lines = len(correct_fix.strip().split("\n"))
        submitted_lines = len(fixed_code.strip().split("\n"))
        line_diff = abs(correct_lines - submitted_lines)
        length_score = 1.0 if line_diff <= 2 else 0.5

        # Does it remove the bug pattern? (original bad code should not appear)
        original_bad = snippet["code"].strip().split("\n")[snippet["bug_line"] - 1].strip()
        no_regression = 0.0 if original_bad in fixed_code else 1.0

        final = keyword_score * 0.5 + length_score * 0.25 + no_regression * 0.25
        feedback = f"Fix score={final:.2f} (keywords={keyword_score:.1f}, length={length_score:.1f})"
        return round(final, 2), feedback
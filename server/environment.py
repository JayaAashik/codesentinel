"""
server/environment.py — Vortex Vanguard RL Environment (HYBRID FIXED)
"""

import uuid
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict

from data import (
    SNIPPETINDEX, CODESNIPPETS, CODETASKCONFIGS,
    TICKETINDEX, TICKETS, SUPPORTTASKCONFIGS,
    KNOWLEDGEBASE
)

from models import CodeReviewAction, CodeObservation, CodeSentinelState
from server.grader import grade_easy, grade_medium, grade_hard, safe_score


# ✅ BACKWARD COMPATIBILITY
TASK_CONFIGS = CODETASKCONFIGS


# ─────────────────────────────────────────────
# GRADERS
# ─────────────────────────────────────────────

GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}


# ─────────────────────────────────────────────
# MAIN ENVIRONMENT
# ─────────────────────────────────────────────

class VortexVanguardEnvironment:

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

    # ─────────────────────────────────────────────

    def reset(self) -> CodeObservation:
        self._episode_id = str(uuid.uuid4())[:8]
        self._step_count = 0
        self._cumulative_reward = 0.0
        self._bugs_correct = 0
        self._history = []
        self._done = False

        ids = self.config["snippet_ids"]

        # ✅ HYBRID LOADING
        self._snippets = []
        for sid in ids:
            if sid.startswith("c") and sid in SNIPPETINDEX:
                self._snippets.append(SNIPPETINDEX[sid])
            elif sid.startswith("t") and sid in TICKETINDEX:
                self._snippets.append(TICKETINDEX[sid])

        return self._make_observation()

    # ─────────────────────────────────────────────

    def step(self, action: CodeReviewAction):
        if self._done:
            raise RuntimeError("Episode over. Call reset() first.")

        try:
            current = self._snippets[self._step_count]
            snippet_id = current["id"]

            # ✅ HYBRID SWITCH
            if snippet_id.startswith("c"):
                current = SNIPPETINDEX[snippet_id]

            elif snippet_id.startswith("t"):
                current = TICKETINDEX[snippet_id]

            # ✅ ACTION DICT
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

            # ✅ UPDATE STATS
            self._cumulative_reward += reward

            if reward >= 0.65:
                self._bugs_correct += 1

            self._history.append({
                "step": self._step_count,
                "snippet_id": current["id"],
                "reward": reward,
                "correct_bug_type": current.get("bug_type", "unknown"),
                "agent_bug_type": action.bug_type,
            })

            self._step_count += 1
            self._done = self._step_count >= len(self._snippets)

            obs = self._make_observation()
            obs.reward = reward
            obs.feedback = f"reward={reward:.4f}"

            info = {
                "snippet_id": current["id"],
                "reward": reward,
                "cumulative_reward": round(self._cumulative_reward, 4),
                "bugs_correct": self._bugs_correct,
            }

            return obs, reward, self._done, info

        except RuntimeError:
            raise

        except Exception as e:
            # SAFE FALLBACK
            self._step_count += 1
            self._done = self._step_count >= len(self._snippets)

            obs = self._make_observation()

            return obs, 0.50, self._done, {
                "error": str(e),
                "reward": 0.50
            }

    # ─────────────────────────────────────────────

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

    # ─────────────────────────────────────────────

    def _make_observation(self) -> CodeObservation:

        if self._done or self._step_count >= len(self._snippets):
            return CodeObservation(
                snippet_id="done",
                title="Episode Complete",
                language="python",
                code="",
                task_description=f"Completed {self.task} task.",
                step=self._step_count,
                total_snippets=len(self._snippets),
                done=True,
            )

        s = self._snippets[self._step_count]

        return CodeObservation(
            snippet_id=s["id"],
            title=s.get("title", "Unknown"),
            language=s.get("language", "python"),
            code=s.get("code", ""),
            task_description=self.config["description"],
            step=self._step_count,
            total_snippets=len(self._snippets),
            done=False,
        )

    # ─────────────────────────────────────────────

    def grade_episode(self) -> Dict:

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

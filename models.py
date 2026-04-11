from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

VALID_BUG_TYPES = [
    "security", "logic", "performance",
    "null_reference", "exception_handling"
]


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


@dataclass
class CodeReviewAction:
    bug_type: str
    severity: int = 3
    bug_line: int = 1
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.bug_type, str):
            self.bug_type = "logic"
        self.bug_type = self.bug_type.lower().strip().replace(" ", "_")
        if self.bug_type not in VALID_BUG_TYPES:
            self.bug_type = "logic"
        try:
            self.severity = _clamp(int(self.severity), 1, 5)
        except Exception:
            self.severity = 3
        try:
            self.bug_line = max(1, int(self.bug_line))
        except Exception:
            self.bug_line = 1
        if self.fixed_code is not None:
            self.fixed_code = str(self.fixed_code)
        if self.explanation is not None:
            self.explanation = str(self.explanation)


@dataclass
class CodeObservation:
    snippet_id: str
    title: str
    language: str
    code: str
    task_description: str
    step: int
    total_snippets: int
    done: bool = False
    reward: Optional[float] = None
    feedback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeSentinelState:
    episode_id: Optional[str]
    step_count: int
    task: str
    total_snippets: int
    snippets_reviewed: int
    cumulative_reward: float
    bugs_found_correctly: int
    done: bool
    history: List[Dict[str, Any]] = field(default_factory=list)

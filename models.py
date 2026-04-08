from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CodeReviewAction:
    """
    What the agent sends each step.
    
    bug_type  : Category of bug found
    severity  : How critical (1=critical, 5=just info)
    bug_line  : Which line number has the bug
    fixed_code: The corrected version of the code (hard task only)
    explanation: Brief explanation of the bug
    """
    bug_type: str                    # security | logic | performance | null_reference | exception_handling
    severity: int = 3                # 1=critical, 2=high, 3=medium, 4=low, 5=info
    bug_line: int = 1                # Line number where bug is
    fixed_code: Optional[str] = None # Corrected code (hard task)
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeObservation:
    """
    What the agent sees — one buggy code snippet at a time.
    """
    snippet_id: str
    title: str
    language: str
    code: str                        # The buggy code to review
    task_description: str
    step: int
    total_snippets: int
    done: bool = False
    reward: Optional[float] = None
    feedback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeSentinelState:
    """
    Full environment state.
    """
    episode_id: Optional[str]
    step_count: int
    task: str
    total_snippets: int
    snippets_reviewed: int
    cumulative_reward: float
    bugs_found_correctly: int
    done: bool
    history: List[Dict[str, Any]] = field(default_factory=list)
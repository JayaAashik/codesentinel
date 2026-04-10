import random

BASE_SNIPPETS = [
    {
        "id": "c001",
        "title": "SQL Injection",
        "language": "python",
        "code": "query = f\"SELECT * FROM users WHERE username='{username}'\"",
        "bug_type": "security",
        "severity": 1,
        "bug_line": 1,
        "fix_keywords": ["parameterized"],
        "fixed_code": "query = \"SELECT * FROM users WHERE username=?\"",
    },
    {
        "id": "c002",
        "title": "Hardcoded Secret",
        "language": "python",
        "code": "API_KEY = 'SECRET123'",
        "bug_type": "security",
        "severity": 1,
        "bug_line": 1,
        "fix_keywords": ["os.getenv"],
        "fixed_code": "import os\nAPI_KEY = os.getenv('API_KEY')",
    }
]

BUG_TEMPLATES = [
    {
        "type": "logic",
        "code": [
            "for i in range(len(arr)+1): print(arr[i])",
            "if x > 5:\n print('ok')\nelse:\n print('ok')",
        ],
        "fix": [
            "for i in range(len(arr)): print(arr[i])",
            "fix condition logic"
        ],
        "severity": 3,
        "line": [1]
    },
    {
        "type": "runtime",
        "code": [
            "lst=[1,2,3]\nprint(lst[10])",
            "def f(): return x\nf()"
        ],
        "fix": [
            "print(lst[-1])",
            "initialize x before use"
        ],
        "severity": 2,
        "line": [2,1]
    },
    {
        "type": "type",
        "code": [
            "print(5 + '5')",
            "a=10\nb='2'\nprint(a+b)"
        ],
        "fix": [
            "print(5 + int('5'))",
            "convert types properly"
        ],
        "severity": 3,
        "line": [1,2]
    },
    {
        "type": "performance",
        "code": [
            "def fib(n): return fib(n-1)+fib(n-2)",
            "for i in range(10000):\n for j in range(10000): pass"
        ],
        "fix": [
            "use memoization",
            "optimize nested loops"
        ],
        "severity": 4,
        "line": [1]
    },
    {
        "type": "null_reference",
        "code": [
            "def f(x): return len(x)",
            "user=None\nprint(user.name)"
        ],
        "fix": [
            "return len(x) if x else 0",
            "check for None"
        ],
        "severity": 2,
        "line": [1,2]
    },
    {
        "type": "exception_handling",
        "code": [
            "try:\n x=1\nexcept:\n pass",
            "try:\n open('file')\nexcept Exception:\n pass"
        ],
        "fix": [
            "handle specific exception",
            "log error properly"
        ],
        "severity": 3,
        "line": [2,3]
    }
]

AUTO_SNIPPETS = []

for i in range(3, 75):
    template = random.choice(BUG_TEMPLATES)
    idx = random.randint(0, len(template["code"]) - 1)

    AUTO_SNIPPETS.append({
        "id": f"c{i:03}",
        "title": f"Auto Bug {i}",
        "language": "python",
        "code": template["code"][idx],
        "bug_type": template["type"],
        "severity": template["severity"],
        "bug_line": random.choice(template["line"]),
        "fix_keywords": ["fix", "correct"],
        "fixed_code": template["fix"][idx],
    })

CODE_SNIPPETS = BASE_SNIPPETS + AUTO_SNIPPETS
SNIPPET_INDEX = {s["id"]: s for s in CODE_SNIPPETS}

TASK_CONFIGS = {
    "easy": {
        "description": "Identify bug type only",
        "snippet_ids": [s["id"] for s in CODE_SNIPPETS[:10]],
        "require_severity": False,
        "require_line": False,
        "require_fix": False,
        "weights": {"bug_type": 1.0}
    },
    "medium": {
        "description": "Identify bug type, severity, and line",
        "snippet_ids": [s["id"] for s in CODE_SNIPPETS[10:35]],
        "require_severity": True,
        "require_line": True,
        "require_fix": False,
        "weights": {"bug_type": 0.5, "severity": 0.25, "line": 0.25}
    },
    "hard": {
        "description": "Full bug detection and fix",
        "snippet_ids": [s["id"] for s in CODE_SNIPPETS[35:70]],
        "require_severity": True,
        "require_line": True,
        "require_fix": True,
        "weights": {"bug_type": 0.25, "severity": 0.15, "line": 0.15, "fix": 0.45}
    }
}

"""
CodeSentinel Data — 75+ Real-World Python Bug Snippets
=======================================================
Hybrid: 15 expert-crafted base snippets + 60 auto-generated variants.
Covers 5 bug categories across easy/medium/hard difficulty splits.
"""

import random

random.seed(2024)

# ── 15 Expert-Crafted Base Snippets ──────────────────────────────────────────

BASE_SNIPPETS = [
    # SECURITY
    {
        "id": "c001",
        "title": "SQL Injection in Login",
        "language": "python",
        "code": (
            'def login(username, password):\n'
            '    query = f"SELECT * FROM users WHERE username=\'{username}\' AND password=\'{password}\'"\n'
            '    result = db.execute(query)\n'
            '    return len(result) > 0'
        ),
        "bug_type": "security",
        "severity": 1,
        "bug_line": 2,
        "fix_keywords": ["parameterized", "?", "prepared", "execute(query,"],
        "fixed_code": (
            'def login(username, password):\n'
            '    query = "SELECT * FROM users WHERE username=? AND password=?"\n'
            '    result = db.execute(query, (username, password))\n'
            '    return len(result) > 0'
        ),
    },
    {
        "id": "c002",
        "title": "Hardcoded Credentials",
        "language": "python",
        "code": (
            'class Config:\n'
            '    DATABASE_URL = "postgresql://admin:password123@localhost/prod"\n'
            '    API_SECRET = "sk-abc123secretkey456789"\n'
            '    DEBUG = True'
        ),
        "bug_type": "security",
        "severity": 1,
        "bug_line": 2,
        "fix_keywords": ["os.environ", "getenv", "environment variable", ".env"],
        "fixed_code": (
            'import os\n\n'
            'class Config:\n'
            '    DATABASE_URL = os.environ.get("DATABASE_URL")\n'
            '    API_SECRET = os.environ.get("API_SECRET")\n'
            '    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"'
        ),
    },
    {
        "id": "c003",
        "title": "Weak MD5 Password Hash",
        "language": "python",
        "code": (
            'import hashlib\n\n'
            'def store_password(password):\n'
            '    hashed = hashlib.md5(password.encode()).hexdigest()\n'
            '    db.save_password(hashed)'
        ),
        "bug_type": "security",
        "severity": 1,
        "bug_line": 4,
        "fix_keywords": ["bcrypt", "argon2", "sha256", "salt", "hashpw"],
        "fixed_code": (
            'import bcrypt\n\n'
            'def store_password(password):\n'
            '    salt = bcrypt.gensalt()\n'
            '    hashed = bcrypt.hashpw(password.encode(), salt)\n'
            '    db.save_password(hashed)'
        ),
    },
    # LOGIC
    {
        "id": "c004",
        "title": "Off-By-One IndexError",
        "language": "python",
        "code": (
            'def find_max(arr):\n'
            '    max_val = arr[0]\n'
            '    for i in range(len(arr) + 1):\n'
            '        if arr[i] > max_val:\n'
            '            max_val = arr[i]\n'
            '    return max_val'
        ),
        "bug_type": "logic",
        "severity": 2,
        "bug_line": 3,
        "fix_keywords": ["range(len(arr))", "range(1,", "len(arr))"],
        "fixed_code": (
            'def find_max(arr):\n'
            '    max_val = arr[0]\n'
            '    for i in range(1, len(arr)):\n'
            '        if arr[i] > max_val:\n'
            '            max_val = arr[i]\n'
            '    return max_val'
        ),
    },
    {
        "id": "c005",
        "title": "Weak Email Validator",
        "language": "python",
        "code": (
            'def is_valid_email(email):\n'
            '    if "@" in email:\n'
            '        return True\n'
            '    return False'
        ),
        "bug_type": "logic",
        "severity": 3,
        "bug_line": 2,
        "fix_keywords": ["regex", "re.match", "pattern", "domain"],
        "fixed_code": (
            'import re\n\n'
            'def is_valid_email(email):\n'
            '    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"\n'
            '    return bool(re.match(pattern, email))'
        ),
    },
    {
        "id": "c006",
        "title": "Case-Sensitive Role Check",
        "language": "python",
        "code": (
            'def is_admin(role):\n'
            '    if role == "admin" or role == "Admin" or role == "ADMIN":\n'
            '        return True\n'
            '    return False'
        ),
        "bug_type": "logic",
        "severity": 3,
        "bug_line": 2,
        "fix_keywords": ["lower()", ".lower()", "casefold"],
        "fixed_code": 'def is_admin(role):\n    return role.lower() == "admin"',
    },
    # PERFORMANCE
    {
        "id": "c007",
        "title": "N+1 Database Queries",
        "language": "python",
        "code": (
            'def get_all_orders(user_ids):\n'
            '    orders = []\n'
            '    for uid in user_ids:\n'
            '        user_orders = db.query(f"SELECT * FROM orders WHERE user_id={uid}")\n'
            '        orders.extend(user_orders)\n'
            '    return orders'
        ),
        "bug_type": "performance",
        "severity": 3,
        "bug_line": 3,
        "fix_keywords": ["IN", "batch", "WHERE user_id IN"],
        "fixed_code": (
            'def get_all_orders(user_ids):\n'
            '    placeholders = ",".join(["?"] * len(user_ids))\n'
            '    query = f"SELECT * FROM orders WHERE user_id IN ({placeholders})"\n'
            '    return db.query(query, user_ids)'
        ),
    },
    {
        "id": "c008",
        "title": "Exponential Fibonacci",
        "language": "python",
        "code": (
            'def fibonacci(n):\n'
            '    if n <= 1:\n'
            '        return n\n'
            '    return fibonacci(n - 1) + fibonacci(n - 2)'
        ),
        "bug_type": "performance",
        "severity": 3,
        "bug_line": 4,
        "fix_keywords": ["lru_cache", "memo", "cache", "iterative"],
        "fixed_code": (
            'from functools import lru_cache\n\n'
            '@lru_cache(maxsize=None)\n'
            'def fibonacci(n):\n'
            '    if n <= 1:\n'
            '        return n\n'
            '    return fibonacci(n - 1) + fibonacci(n - 2)'
        ),
    },
    {
        "id": "c009",
        "title": "O(n²) Duplicate Removal",
        "language": "python",
        "code": (
            'def remove_duplicates(items):\n'
            '    result = []\n'
            '    for item in items:\n'
            '        if item not in result:\n'
            '            result.append(item)\n'
            '    return result'
        ),
        "bug_type": "performance",
        "severity": 4,
        "bug_line": 4,
        "fix_keywords": ["set", "seen", "dict"],
        "fixed_code": (
            'def remove_duplicates(items):\n'
            '    seen = set()\n'
            '    result = []\n'
            '    for item in items:\n'
            '        if item not in seen:\n'
            '            seen.add(item)\n'
            '            result.append(item)\n'
            '    return result'
        ),
    },
    # NULL REFERENCE
    {
        "id": "c010",
        "title": "None Text Processing",
        "language": "python",
        "code": (
            'def get_string_info(text):\n'
            '    length = len(text)\n'
            '    words = text.split()\n'
            '    return {"length": length, "words": len(words)}'
        ),
        "bug_type": "null_reference",
        "severity": 2,
        "bug_line": 2,
        "fix_keywords": ["None", "if text", "is None", "not text"],
        "fixed_code": (
            'def get_string_info(text):\n'
            '    if text is None:\n'
            '        return {"length": 0, "words": 0}\n'
            '    return {"length": len(text), "words": len(text.split())}'
        ),
    },
    {
        "id": "c011",
        "title": "Missing Key Access",
        "language": "python",
        "code": (
            'import json\n\n'
            'def get_timeout(config_str):\n'
            '    data = json.loads(config_str)\n'
            '    return data["settings"]["timeout"]'
        ),
        "bug_type": "null_reference",
        "severity": 2,
        "bug_line": 5,
        "fix_keywords": [".get(", "KeyError", "try", "except"],
        "fixed_code": (
            'import json\n\n'
            'def get_timeout(config_str):\n'
            '    try:\n'
            '        data = json.loads(config_str)\n'
            '        return data.get("settings", {}).get("timeout", 30)\n'
            '    except (json.JSONDecodeError, KeyError):\n'
            '        return 30'
        ),
    },
    # EXCEPTION HANDLING
    {
        "id": "c012",
        "title": "Silent Payment Failure",
        "language": "python",
        "code": (
            'def process_payment(amount, card):\n'
            '    try:\n'
            '        result = payment_gateway.charge(amount, card)\n'
            '        return result\n'
            '    except:\n'
            '        pass'
        ),
        "bug_type": "exception_handling",
        "severity": 2,
        "bug_line": 5,
        "fix_keywords": ["except Exception", "log", "raise", "logger"],
        "fixed_code": (
            'def process_payment(amount, card):\n'
            '    try:\n'
            '        result = payment_gateway.charge(amount, card)\n'
            '        return result\n'
            '    except Exception as e:\n'
            '        logger.error(f"Payment failed: {e}")\n'
            '        raise'
        ),
    },
    {
        "id": "c013",
        "title": "Unclosed File Handle",
        "language": "python",
        "code": (
            'def read_config(filepath):\n'
            '    f = open(filepath)\n'
            '    content = f.read()\n'
            '    return content'
        ),
        "bug_type": "exception_handling",
        "severity": 3,
        "bug_line": 2,
        "fix_keywords": ["with open", "finally", "context manager"],
        "fixed_code": 'def read_config(filepath):\n    with open(filepath) as f:\n        return f.read()',
    },
    {
        "id": "c014",
        "title": "Division By Zero",
        "language": "python",
        "code": 'def calculate_average(total, count):\n    return total / count',
        "bug_type": "exception_handling",
        "severity": 2,
        "bug_line": 2,
        "fix_keywords": ["ZeroDivisionError", "if count", "count == 0", "try"],
        "fixed_code": (
            'def calculate_average(total, count):\n'
            '    if count == 0:\n'
            '        return 0.0\n'
            '    return total / count'
        ),
    },
    {
        "id": "c015",
        "title": "Hard-Coded Index",
        "language": "python",
        "code": 'def get_top_three(items):\n    return [items[0], items[1], items[2]]',
        "bug_type": "logic",
        "severity": 2,
        "bug_line": 2,
        "fix_keywords": ["len", "slice", "items[:3]", "if len"],
        "fixed_code": 'def get_top_three(items):\n    return items[:3]',
    },
]

# ── Auto-Generation Templates ─────────────────────────────────────────────────

_TEMPLATES = [
    {
        "type": "logic",
        "severity": 3,
        "variants": [
            (
                "def count_words_{i}(text):\n    words = text.split(' ')\n    return len(words) + 1",
                "def count_words_{i}(text):\n    return len(text.split())",
                3, ["len", "split", "strip"]
            ),
            (
                "def is_even_{i}(n):\n    return n % 2 == 1",
                "def is_even_{i}(n):\n    return n % 2 == 0",
                2, ["% 2 == 0", "modulo", "even"]
            ),
            (
                "def max_of_two_{i}(a, b):\n    if a > b:\n        return b\n    return a",
                "def max_of_two_{i}(a, b):\n    return a if a > b else b",
                2, ["return a", "max", "greater"]
            ),
        ],
    },
    {
        "type": "security",
        "severity": 1,
        "variants": [
            (
                "SECRET_KEY_{i} = 'hardcoded-secret-key-abc123'",
                "import os\nSECRET_KEY_{i} = os.getenv('SECRET_KEY_{i}')",
                1, ["os.getenv", "environment", "getenv"]
            ),
            (
                "def get_user_{i}(user_id):\n    return db.execute('SELECT * FROM users WHERE id=' + str(user_id))",
                "def get_user_{i}(user_id):\n    return db.execute('SELECT * FROM users WHERE id=?', (user_id,))",
                2, ["parameterized", "?", "execute("]
            ),
            (
                "PASSWORD_{i} = 'admin123'",
                "import os\nPASSWORD_{i} = os.getenv('PASSWORD_{i}')",
                1, ["os.getenv", "environment"]
            ),
        ],
    },
    {
        "type": "performance",
        "severity": 4,
        "variants": [
            (
                "def concat_{i}(words):\n    result = ''\n    for w in words:\n        result = result + w\n    return result",
                "def concat_{i}(words):\n    return ''.join(words)",
                3, ["join", "string", "efficient"]
            ),
            (
                "def find_{i}(items, val):\n    for i in range(len(items)):\n        if items[i] == val:\n            return i\n    return -1",
                "def find_{i}(items, val):\n    try:\n        return items.index(val)\n    except ValueError:\n        return -1",
                2, ["index", "efficient", "built-in"]
            ),
            (
                "def squares_{i}(n):\n    result = []\n    for i in range(n):\n        result.append(i * i)\n    return result",
                "def squares_{i}(n):\n    return [i * i for i in range(n)]",
                2, ["list comprehension", "efficient"]
            ),
        ],
    },
    {
        "type": "null_reference",
        "severity": 2,
        "variants": [
            (
                "def upper_{i}(s):\n    return s.upper()",
                "def upper_{i}(s):\n    return s.upper() if s else ''",
                2, ["None", "if s", "is None"]
            ),
            (
                "def first_{i}(lst):\n    return lst[0]",
                "def first_{i}(lst):\n    return lst[0] if lst else None",
                2, ["if lst", "empty", "None"]
            ),
            (
                "def get_name_{i}(obj):\n    return obj['name']",
                "def get_name_{i}(obj):\n    return obj.get('name', '') if obj else ''",
                2, [".get(", "None", "empty"]
            ),
        ],
    },
    {
        "type": "exception_handling",
        "severity": 3,
        "variants": [
            (
                "def parse_int_{i}(s):\n    try:\n        return int(s)\n    except:\n        pass",
                "def parse_int_{i}(s):\n    try:\n        return int(s)\n    except ValueError:\n        return None",
                3, ["ValueError", "specific", "return None"]
            ),
            (
                "def read_file_{i}(path):\n    return open(path).read()",
                "def read_file_{i}(path):\n    with open(path) as f:\n        return f.read()",
                2, ["with open", "context manager"]
            ),
            (
                "def safe_div_{i}(a, b):\n    try:\n        return a / b\n    except:\n        return 0",
                "def safe_div_{i}(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return 0",
                2, ["ZeroDivisionError", "specific exception"]
            ),
        ],
    },
]

# ── Generate 60 additional snippets ──────────────────────────────────────────

AUTO_SNIPPETS = []

for idx in range(16, 76):
    tmpl_idx = (idx - 16) % len(_TEMPLATES)
    tmpl = _TEMPLATES[tmpl_idx]
    var_idx = (idx - 16) // len(_TEMPLATES) % len(tmpl["variants"])
    code_tpl, fix_tpl, bug_line, kws = tmpl["variants"][var_idx]

    code = code_tpl.format(i=idx)
    fix = fix_tpl.format(i=idx)

    AUTO_SNIPPETS.append({
        "id": f"c{idx:03d}",
        "title": f"Auto {tmpl['type'].replace('_', ' ').title()} Bug #{idx}",
        "language": "python",
        "code": code,
        "bug_type": tmpl["type"],
        "severity": tmpl["severity"],
        "bug_line": bug_line,
        "fix_keywords": kws,
        "fixed_code": fix,
    })

# ── Final Dataset ─────────────────────────────────────────────────────────────

CODE_SNIPPETS = BASE_SNIPPETS + AUTO_SNIPPETS

assert len(CODE_SNIPPETS) >= 75, f"Need 75+ snippets, got {len(CODE_SNIPPETS)}"

SNIPPET_INDEX = {s["id"]: s for s in CODE_SNIPPETS}
VALID_BUG_TYPES = ["security", "logic", "performance", "null_reference", "exception_handling"]
VALID_SEVERITIES = [1, 2, 3, 4, 5]

# ── Task Configurations ───────────────────────────────────────────────────────

TASK_CONFIGS = {
    "easy": {
        "description": "Identify the bug TYPE in each code snippet (security/logic/performance/null_reference/exception_handling).",
        "snippet_ids": [s["id"] for s in CODE_SNIPPETS[:10]],
        "require_severity": False,
        "require_line": False,
        "require_fix": False,
        "weights": {"bug_type": 1.0, "severity": 0.0, "line": 0.0, "fix": 0.0},
    },
    "medium": {
        "description": "Identify bug TYPE + SEVERITY (1=critical..5=info) + which LINE number contains the bug.",
        "snippet_ids": [s["id"] for s in CODE_SNIPPETS[10:30]],
        "require_severity": True,
        "require_line": True,
        "require_fix": False,
        "weights": {"bug_type": 0.50, "severity": 0.25, "line": 0.25, "fix": 0.0},
    },
    "hard": {
        "description": "Identify bug TYPE + SEVERITY + LINE + write the complete FIXED code.",
        "snippet_ids": [s["id"] for s in CODE_SNIPPETS[30:55]],
        "require_severity": True,
        "require_line": True,
        "require_fix": True,
        "weights": {"bug_type": 0.25, "severity": 0.15, "line": 0.15, "fix": 0.45},
    },
}

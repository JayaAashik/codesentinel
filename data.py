"""
Combined Dataset: CodeSentinel + Vortex Vanguard
=================================================
CodeSentinel: 75+ Real-World Python Bug Snippets
Vortex Vanguard: Customer Support RL Environment
"""

import random

random.seed(2024)

# ==============================================================================
# CODESENTINEL DATA — Bug Detection Snippets
# ==============================================================================

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

# ── Final CodeSentinel Dataset ────────────────────────────────────────────────

CODE_SNIPPETS = BASE_SNIPPETS + AUTO_SNIPPETS

assert len(CODE_SNIPPETS) >= 75, f"Need 75+ snippets, got {len(CODE_SNIPPETS)}"

SNIPPET_INDEX = {s["id"]: s for s in CODE_SNIPPETS}
VALID_BUG_TYPES = ["security", "logic", "performance", "null_reference", "exception_handling"]
VALID_SEVERITIES = [1, 2, 3, 4, 5]

# ── CodeSentinel Task Configurations ──────────────────────────────────────────

CODE_TASK_CONFIGS = {
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


# ==============================================================================
# VORTEX VANGUARD DATA — Customer Support Environment
# ==============================================================================

# ── Knowledge Base (what agent can "look up") ─────────────────────────────────
KNOWLEDGE_BASE = {
    "refund_policy": {
        "content": "Full refund available within 30 days of purchase. After 30 days, store credit only. No refund on digital downloads after access. Premium members get 60-day refund window.",
        "keywords": ["refund", "money back", "return", "charged", "payment"]
    },
    "password_reset": {
        "content": "Click 'Forgot Password' on login page. Enter email. Check inbox (and spam). Link expires in 2 hours. If no email after 10 minutes, check spam or try alternate email.",
        "keywords": ["password", "login", "reset", "access", "forgot"]
    },
    "shipping_policy": {
        "content": "Standard shipping 5-7 business days. Express 2-3 days. International 10-14 days. Free shipping on orders over $50. Tracking provided via email.",
        "keywords": ["shipping", "delivery", "order", "track", "arrive", "package"]
    },
    "cancellation_policy": {
        "content": "Cancel anytime before renewal date. No penalty for cancellation. Subscription continues until end of billing period. Refund not available for partial months.",
        "keywords": ["cancel", "subscription", "billing", "renew", "stop"]
    },
    "technical_escalation": {
        "content": "Escalate to Tier 2 tech if: issue unresolved after 2 contacts, data loss involved, service down >2 hours, enterprise client affected.",
        "keywords": ["crash", "broken", "error", "not working", "bug", "technical"]
    },
    "vip_policy": {
        "content": "VIP/Premium customers get: priority queue (response within 1 hour), dedicated agent, 2x refund window, free express shipping, personal account manager.",
        "keywords": ["vip", "premium", "enterprise", "priority", "urgent"]
    },
    "discount_policy": {
        "content": "Discounts available for: loyalty (1yr+), students (with .edu email), bulk orders (10+), referrals. Max 30% discount per order. Cannot combine discounts.",
        "keywords": ["discount", "coupon", "promo", "offer", "deal", "price"]
    },
}

# ── 30 High-Quality Support Tickets ──────────────────────────────────────────

TICKETS = [
    # ── EASY TICKETS (clear single action needed) ─────────────────────────────
    {
        "id": "t001",
        "customer_name": "Priya Sharma",
        "account_tier": "standard",
        "sentiment": "neutral",
        "previous_contacts": 0,
        "subject": "How to reset my password?",
        "message": "Hi, I forgot my password and cannot log in. Can you help?",
        "issue_category": "account_access",
        "correct_kb_key": "password_reset",
        "correct_action": "resolve",
        "correct_priority": "low",
        "requires_escalation": False,
        "correct_reply_tone": "helpful",
        "key_info_needed": ["email", "login", "reset link"],
        "good_reply_keywords": ["reset", "email", "link", "password", "minutes", "spam"],
        "resolution_steps": ["ask for email", "send reset link", "check spam"],
    },
    {
        "id": "t002",
        "customer_name": "Ravi Kumar",
        "account_tier": "standard",
        "sentiment": "neutral",
        "previous_contacts": 0,
        "subject": "Where is my order?",
        "message": "I placed order #12345 last week. It still hasn't arrived. Can you check?",
        "issue_category": "shipping",
        "correct_kb_key": "shipping_policy",
        "correct_action": "gather_info",
        "correct_priority": "medium",
        "requires_escalation": False,
        "correct_reply_tone": "professional",
        "key_info_needed": ["order number", "address", "tracking"],
        "good_reply_keywords": ["track", "order", "shipping", "business days", "email"],
        "resolution_steps": ["verify order", "check tracking", "update customer"],
    },
    {
        "id": "t003",
        "customer_name": "Anjali Nair",
        "account_tier": "standard",
        "sentiment": "neutral",
        "previous_contacts": 0,
        "subject": "How do I cancel my subscription?",
        "message": "I want to cancel my monthly subscription. How do I do this?",
        "issue_category": "subscription",
        "correct_kb_key": "cancellation_policy",
        "correct_action": "resolve",
        "correct_priority": "low",
        "requires_escalation": False,
        "correct_reply_tone": "helpful",
        "key_info_needed": ["account", "billing date", "cancellation steps"],
        "good_reply_keywords": ["cancel", "settings", "billing", "end of period", "continue"],
        "resolution_steps": ["explain cancellation steps", "confirm billing end date"],
    },
    {
        "id": "t004",
        "customer_name": "Suresh Patel",
        "account_tier": "premium",
        "sentiment": "neutral",
        "previous_contacts": 0,
        "subject": "Need a student discount",
        "message": "I am a student. Do you offer any discounts for students?",
        "issue_category": "billing",
        "correct_kb_key": "discount_policy",
        "correct_action": "gather_info",
        "correct_priority": "low",
        "requires_escalation": False,
        "correct_reply_tone": "friendly",
        "key_info_needed": [".edu email", "verification", "discount amount"],
        "good_reply_keywords": ["student", ".edu", "discount", "verify", "email"],
        "resolution_steps": ["confirm .edu email", "apply discount"],
    },
    {
        "id": "t005",
        "customer_name": "Meera Joshi",
        "account_tier": "standard",
        "sentiment": "neutral",
        "previous_contacts": 0,
        "subject": "Want to check refund policy",
        "message": "I bought a product 2 weeks ago. Is it too late for a refund?",
        "issue_category": "refund",
        "correct_kb_key": "refund_policy",
        "correct_action": "resolve",
        "correct_priority": "medium",
        "requires_escalation": False,
        "correct_reply_tone": "helpful",
        "key_info_needed": ["purchase date", "product type", "reason"],
        "good_reply_keywords": ["30 days", "eligible", "refund", "process", "order"],
        "resolution_steps": ["confirm purchase date", "initiate refund", "confirm timeline"],
    },
    # ── MEDIUM TICKETS (require KB lookup + multi-step) ──────────────────────
    {
        "id": "t006",
        "customer_name": "Deepak Singh",
        "account_tier": "standard",
        "sentiment": "frustrated",
        "previous_contacts": 1,
        "subject": "Charged twice this month",
        "message": "I see two charges on my credit card this month. I only have one subscription. Please fix this immediately.",
        "issue_category": "billing",
        "correct_kb_key": "refund_policy",
        "correct_action": "escalate",
        "correct_priority": "high",
        "requires_escalation": True,
        "correct_reply_tone": "apologetic",
        "key_info_needed": ["transaction IDs", "account email", "bank statement"],
        "good_reply_keywords": ["apologize", "investigate", "refund", "billing team", "urgently"],
        "resolution_steps": ["apologize", "gather transaction IDs", "escalate to billing", "confirm timeline"],
    },
    {
        "id": "t007",
        "customer_name": "Kavitha Reddy",
        "account_tier": "premium",
        "sentiment": "frustrated",
        "previous_contacts": 0,
        "subject": "App crashes when uploading files",
        "message": "Every time I try to upload a PDF the app crashes. This is affecting my work. I need this fixed today.",
        "issue_category": "technical",
        "correct_kb_key": "technical_escalation",
        "correct_action": "escalate",
        "correct_priority": "high",
        "requires_escalation": True,
        "correct_reply_tone": "empathetic",
        "key_info_needed": ["device", "app version", "file size", "error message"],
        "good_reply_keywords": ["apologize", "technical team", "urgent", "workaround", "investigate"],
        "resolution_steps": ["gather device info", "escalate to tech", "provide workaround if possible"],
    },
    {
        "id": "t008",
        "customer_name": "Vikram Shah",
        "account_tier": "standard",
        "sentiment": "angry",
        "previous_contacts": 2,
        "subject": "Still not resolved after 2 contacts",
        "message": "I've contacted support twice about this billing error and it's STILL not fixed. This is unacceptable. I want to speak to a manager.",
        "issue_category": "billing",
        "correct_kb_key": "technical_escalation",
        "correct_action": "escalate",
        "correct_priority": "urgent",
        "requires_escalation": True,
        "correct_reply_tone": "apologetic",
        "key_info_needed": ["previous ticket IDs", "account details"],
        "good_reply_keywords": ["sincerely apologize", "manager", "priority", "resolve", "immediately"],
        "resolution_steps": ["acknowledge failure", "escalate to manager", "set resolution timeline"],
    },
    {
        "id": "t009",
        "customer_name": "Sanjana Iyer",
        "account_tier": "premium",
        "sentiment": "frustrated",
        "previous_contacts": 0,
        "subject": "Order delivered but wrong item",
        "message": "I ordered the Pro package but received the Basic one. I am a premium member and this is very disappointing.",
        "issue_category": "shipping",
        "correct_kb_key": "refund_policy",
        "correct_action": "replace",
        "correct_priority": "high",
        "requires_escalation": False,
        "correct_reply_tone": "apologetic",
        "key_info_needed": ["order number", "account verification", "return address"],
        "good_reply_keywords": ["apologize", "correct order", "ship", "premium", "priority"],
        "resolution_steps": ["apologize", "verify order", "ship correct item", "provide return label"],
    },
    {
        "id": "t010",
        "customer_name": "Arjun Mehta",
        "account_tier": "standard",
        "sentiment": "frustrated",
        "previous_contacts": 0,
        "subject": "Cannot access my account data",
        "message": "I logged in but all my saved data is gone. I had months of work in there. Please help ASAP.",
        "issue_category": "technical",
        "correct_kb_key": "technical_escalation",
        "correct_action": "escalate",
        "correct_priority": "urgent",
        "requires_escalation": True,
        "correct_reply_tone": "empathetic",
        "key_info_needed": ["account ID", "last login date", "data type"],
        "good_reply_keywords": ["sorry", "data recovery", "technical team", "urgent", "backup"],
        "resolution_steps": ["gather account info", "escalate to data team", "check backups"],
    },
    # ── HARD TICKETS (complex, multi-issue, requires judgment) ───────────────
    {
        "id": "t011",
        "customer_name": "Lakshmi Venkat",
        "account_tier": "premium",
        "sentiment": "angry",
        "previous_contacts": 3,
        "subject": "Demanding full refund + compensation",
        "message": "I have been a premium customer for 3 years. The service has degraded massively. I want a full refund for this month AND compensation for my time wasted. I will post reviews everywhere if this is not resolved.",
        "issue_category": "complaint",
        "correct_kb_key": "vip_policy",
        "correct_action": "escalate",
        "correct_priority": "urgent",
        "requires_escalation": True,
        "correct_reply_tone": "apologetic",
        "key_info_needed": ["specific issues", "dates", "impact assessment"],
        "good_reply_keywords": ["value", "premium", "escalate", "manager", "personally", "resolve", "apologize"],
        "resolution_steps": ["acknowledge loyalty", "apologize genuinely", "escalate to retention team", "offer compensation"],
    },
    {
        "id": "t012",
        "customer_name": "Raj Nambiar",
        "account_tier": "enterprise",
        "sentiment": "angry",
        "previous_contacts": 1,
        "subject": "Service down affecting 200 employees",
        "message": "Our entire team of 200 people cannot use the service since this morning. We are losing money every minute. This is a business emergency. We need immediate action.",
        "issue_category": "technical",
        "correct_kb_key": "technical_escalation",
        "correct_action": "escalate",
        "correct_priority": "urgent",
        "requires_escalation": True,
        "correct_reply_tone": "urgent_professional",
        "key_info_needed": ["company name", "account ID", "error details", "affected users"],
        "good_reply_keywords": ["immediate", "escalate", "enterprise", "priority", "team", "update every"],
        "resolution_steps": ["acknowledge emergency", "escalate to enterprise support", "set 30-min update cadence"],
    },
    {
        "id": "t013",
        "customer_name": "Pooja Agarwal",
        "account_tier": "standard",
        "sentiment": "neutral",
        "previous_contacts": 0,
        "subject": "Want to upgrade but have questions",
        "message": "I want to upgrade from standard to premium. But I want to know: will I lose my current data? Can I downgrade later if I change my mind? What's the price difference?",
        "issue_category": "subscription",
        "correct_kb_key": "cancellation_policy",
        "correct_action": "resolve",
        "correct_priority": "medium",
        "requires_escalation": False,
        "correct_reply_tone": "enthusiastic",
        "key_info_needed": ["current plan details", "upgrade pricing", "data migration"],
        "good_reply_keywords": ["data", "preserved", "downgrade", "price", "benefit", "upgrade"],
        "resolution_steps": ["answer all 3 questions", "offer upgrade link", "confirm trial period"],
    },
    {
        "id": "t014",
        "customer_name": "Kiran Bose",
        "account_tier": "premium",
        "sentiment": "frustrated",
        "previous_contacts": 0,
        "subject": "Was billed after cancellation",
        "message": "I cancelled my subscription last month and just got charged again. I have the cancellation email. This is fraud.",
        "issue_category": "billing",
        "correct_kb_key": "refund_policy",
        "correct_action": "refund",
        "correct_priority": "urgent",
        "requires_escalation": True,
        "correct_reply_tone": "apologetic",
        "key_info_needed": ["cancellation confirmation", "charge date", "bank details for refund"],
        "good_reply_keywords": ["apologize", "refund", "immediately", "billing error", "process"],
        "resolution_steps": ["verify cancellation email", "confirm charge is error", "process immediate refund", "prevent future charges"],
    },
    {
        "id": "t015",
        "customer_name": "Aditya Rao",
        "account_tier": "standard",
        "sentiment": "happy",
        "previous_contacts": 0,
        "subject": "Referral discount not applied",
        "message": "I referred 3 friends who all signed up. But I never got my referral discount. I have the confirmation emails showing they used my code.",
        "issue_category": "billing",
        "correct_kb_key": "discount_policy",
        "correct_action": "gather_info",
        "correct_priority": "medium",
        "requires_escalation": False,
        "correct_reply_tone": "friendly",
        "key_info_needed": ["referral code", "friend account emails", "confirmation emails"],
        "good_reply_keywords": ["referral", "discount", "apply", "verify", "code", "friends"],
        "resolution_steps": ["verify referral code usage", "confirm 3 signups", "apply discount manually"],
    },
]

# Add 15 more auto-generated tickets for variety
_TICKET_TEMPLATES = [
    {
        "issue_category": "account_access",
        "sentiment": "neutral",
        "correct_action": "resolve",
        "correct_kb_key": "password_reset",
        "correct_priority": "low",
        "requires_escalation": False,
        "subjects": ["Cannot log in", "Account locked", "Two-factor not working"],
        "messages": [
            "I cannot access my account. The password reset email never arrived.",
            "My account seems to be locked. I have not done anything wrong.",
            "My two-factor authentication stopped working after I got a new phone.",
        ],
        "good_reply_keywords": ["reset", "email", "account", "access", "verify"],
    },
    {
        "issue_category": "refund",
        "sentiment": "frustrated",
        "correct_action": "refund",
        "correct_kb_key": "refund_policy",
        "correct_priority": "high",
        "requires_escalation": False,
        "subjects": ["Request refund", "Want money back", "Wrong product refund"],
        "messages": [
            "I want a refund. The product did not meet expectations.",
            "Please refund my purchase from yesterday. I ordered by mistake.",
            "The product I received is defective. I want a full refund.",
        ],
        "good_reply_keywords": ["refund", "process", "days", "account", "apologize"],
    },
    {
        "issue_category": "technical",
        "sentiment": "frustrated",
        "correct_action": "escalate",
        "correct_kb_key": "technical_escalation",
        "correct_priority": "high",
        "requires_escalation": True,
        "subjects": ["App not working", "Feature broken", "Error message"],
        "messages": [
            "The export feature has been broken for 2 days now.",
            "I keep getting an error 500 when I try to save.",
            "The mobile app crashes every time I open it.",
        ],
        "good_reply_keywords": ["technical", "team", "investigate", "sorry", "update"],
    },
]

_NAMES = ["Shreya G", "Ankit B", "Nisha K", "Rohit S", "Divya M", "Aryan P",
          "Tanya R", "Mohan L", "Geeta W", "Farhan Q", "Swathi N", "Krish T"]

for _i in range(16, 31):
    _tmpl = _TICKET_TEMPLATES[(_i - 16) % len(_TICKET_TEMPLATES)]
    _var = (_i - 16) % 3
    TICKETS.append({
        "id": f"t{_i:03d}",
        "customer_name": _NAMES[(_i - 16) % len(_NAMES)],
        "account_tier": ["standard", "premium", "standard"][_var],
        "sentiment": _tmpl["sentiment"],
        "previous_contacts": (_i % 3),
        "subject": _tmpl["subjects"][_var],
        "message": _tmpl["messages"][_var],
        "issue_category": _tmpl["issue_category"],
        "correct_kb_key": _tmpl["correct_kb_key"],
        "correct_action": _tmpl["correct_action"],
        "correct_priority": _tmpl["correct_priority"],
        "requires_escalation": _tmpl["requires_escalation"],
        "correct_reply_tone": "professional",
        "key_info_needed": ["account details"],
        "good_reply_keywords": _tmpl["good_reply_keywords"],
        "resolution_steps": ["identify issue", "take action", "confirm resolution"],
    })

TICKET_INDEX = {t["id"]: t for t in TICKETS}

VALID_ACTIONS = ["resolve", "escalate", "refund", "gather_info", "replace", "transfer"]
VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
VALID_TONES = ["helpful", "apologetic", "empathetic", "professional", "friendly", "urgent_professional"]

# ── Vortex Vanguard Task Configurations ───────────────────────────────────────

SUPPORT_TASK_CONFIGS = {
    "easy": {
        "description": (
            "Read the support ticket and choose the correct ACTION "
            "(resolve/escalate/refund/gather_info). "
            "No reply writing needed."
        ),
        "ticket_ids": [t["id"] for t in TICKETS[:10]],
        "require_kb_search": False,
        "require_reply": False,
        "require_priority": False,
        "weights": {"action": 1.0, "kb": 0.0, "reply": 0.0, "priority": 0.0, "empathy": 0.0},
    },
    "medium": {
        "description": (
            "Read the ticket, search the correct KNOWLEDGE BASE entry, "
            "choose the ACTION, and assign PRIORITY (low/medium/high/urgent). "
            "No reply writing needed."
        ),
        "ticket_ids": [t["id"] for t in TICKETS[5:20]],
        "require_kb_search": True,
        "require_reply": False,
        "require_priority": True,
        "weights": {"action": 0.40, "kb": 0.30, "reply": 0.0, "priority": 0.30, "empathy": 0.0},
    },
    "hard": {
        "description": (
            "Read the ticket, search the knowledge base, choose action + priority, "
            "AND write a professional empathetic reply following company policy. "
            "Score based on action, KB accuracy, reply quality, empathy, and policy compliance."
        ),
        "ticket_ids": [t["id"] for t in TICKETS[5:30]],
        "require_kb_search": True,
        "require_reply": True,
        "require_priority": True,
        "weights": {"action": 0.25, "kb": 0.15, "reply": 0.35, "priority": 0.10, "empathy": 0.15},
    },
}


# ==============================================================================
# UNIFIED TASK CONFIGS (for backward compatibility)
# ==============================================================================

# Default TASK_CONFIGS points to CodeSentinel for backward compatibility
TASK_CONFIGS = CODE_TASK_CONFIGS
# backward compatibility
CODE_SNIPPETS = CODESNIPPETS
SNIPPET_INDEX = SNIPPETINDEX
TASK_CONFIGS = CODETASKCONFIGS

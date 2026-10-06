"""Basic protection against credentials pasted by mistake.

Runs on every text field before anything is sent to the AI service, so obvious secrets
never leave the server. V1 covers well-known key formats and plain "password=..." style
assignments. It is a safety net, not a complete secret scanner.
"""
import re
from typing import List, Tuple

REDACTED = "[REDACTED SECRET]"

# Provider formats are unambiguous, so they are redacted wherever they appear (URLs included).
KEY_PATTERNS = [
    ("private_key", re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----.*?"
        r"(?:-----END [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----|\Z)",
        re.DOTALL,
    )),
    # OpenAI (sk-..., sk-proj-...) and other "sk-" keys such as Anthropic's sk-ant-...
    ("sk_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("slack_token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("stripe_secret_key", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]

# "Bearer <token>": only the token is redacted.
BEARER = re.compile(r"\bBearer\s+(?P<value>[A-Za-z0-9._~+/-]{20,}=*)")

# Assignments such as OPENAI_API_KEY=..., "password": "...", db_password: ... Only the value is redacted.
ASSIGNMENT = re.compile(
    r"(?i)\b[\w-]*?(?:api[ _-]?key|secret|token|password|passwd|pwd|access[ _-]?key|private[ _-]?key)[\w-]*"
    r"[\"']?\s*[:=]\s*[\"']?(?P<value>[^\s\"'`,;]{8,})"
)

URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


def _looks_like_secret(value: str) -> bool:
    # Skips ordinary words after "password:" or "token:" in prose; real values have digits or are long.
    if value.startswith("[REDACTED") or URL.match(value):
        return False
    return any(c.isdigit() for c in value) or len(value) >= 16


def redact_secrets(text: str) -> Tuple[str, List[str]]:
    """Return the text with obvious secrets replaced by REDACTED, and the kinds found (never the values)."""
    if not text:
        return text, []
    kinds: List[str] = []

    for kind, pattern in KEY_PATTERNS:
        text, count = pattern.subn(REDACTED, text)
        kinds.extend([kind] * count)

    def replace_value(match: re.Match, kind: str) -> str:
        if not _looks_like_secret(match.group("value")):
            return match.group(0)
        kinds.append(kind)
        start, end = match.span("value")
        offset = match.start()
        return match.group(0)[: start - offset] + REDACTED + match.group(0)[end - offset:]

    text = BEARER.sub(lambda m: replace_value(m, "bearer_token"), text)

    # The generic assignment rule skips URLs, so query strings such as ?token=... pass through
    # unchanged. Provider key formats above are still redacted inside URLs.
    url_spans = [m.span() for m in URL.finditer(text)]

    def replace_assignment(match: re.Match) -> str:
        if any(start <= match.start() < end for start, end in url_spans):
            return match.group(0)
        return replace_value(match, "secret_assignment")

    text = ASSIGNMENT.sub(replace_assignment, text)
    return text, kinds

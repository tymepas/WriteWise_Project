"""Live golden tests for Prompt mode (cost API credits; skipped unless enabled, see conftest.py).

Each fictional case in prompt_mode_cases.py lists semantic properties the refined message must
have. Passing them catches clear failures but is not proof of intent preservation: the outputs
still need a human read, which these tests print with `pytest -s`.
"""
import os
import re
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prompt_mode_cases import CASES  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Applies to every case: Prompt mode clarifies the user's message, it does not engineer a prompt.
NEVER = {
    "persona or role": r"\byou are an?\b|\bact as\b|\bas an? (expert|experienced|senior)\b",
    "reasoning instructions": r"step[- ]by[- ]step reasoning|think step by step|chain of thought",
    "template sections": r"^\s*(context|goal|objective|requirements|constraints|expected output|additional notes)\s*:",
    "claims to have looked": r"\bI (have )?(visited|opened|watched|reviewed|checked|analy[sz]ed|read) (the|this|your)\b",
    "em dash": "—",
}


def refine(text):
    r = requests.post(f"{BASE_URL}/api/generate", json={"mode": "prompt", "input": text}, timeout=300)
    assert r.status_code == 200, r.text
    return r.json()["output"]


def first(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.start() if match else -1


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_refined_message_keeps_the_meaning(case):
    out = refine(case.input)
    print(f"\n[{case.id}] {case.kind}\n--- input ---\n{case.input}\n--- output ---\n{out}")

    assert out.strip()
    for url in case.urls:
        assert url in out, f"URL changed or missing: {url}"
    for text in case.exact:
        assert text in out, f"technical wording changed: {text!r}"
    for pattern in case.must:
        assert re.search(pattern, out, re.IGNORECASE), f"lost: /{pattern}/"
    for pattern in case.must_not:
        assert not re.search(pattern, out, re.IGNORECASE | re.MULTILINE), f"should not contain: /{pattern}/"
    for name, pattern in NEVER.items():
        assert not re.search(pattern, out, re.IGNORECASE | re.MULTILINE), f"added {name}"

    positions = [first(p, out) for p in case.order]
    assert positions == sorted(positions) and -1 not in positions, f"order changed: {case.order} -> {positions}"

    assert len(out) <= len(case.input) * case.max_ratio, f"grew to {len(out)} chars from {len(case.input)}"
    if case.max_chars:
        assert len(out) <= case.max_chars, f"{len(out)} chars for a short request"
    if case.one_paragraph:
        assert "\n" not in out.strip(), "a simple request became a structured prompt"

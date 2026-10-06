"""Prompt mode and secret redaction tests with a fake OpenAI client. No network calls, no cost.

These check the properties that can be tested deterministically (URLs, empty input, output
handling, redaction, regressions). Whether the model preserves intent is checked by the live
golden tests in tests/integration/test_prompt_mode_live.py and by human review.
"""
import json
import logging
import re

import httpx2
import openai
import pytest
from fastapi.testclient import TestClient

import prompt_mode
import server
from prompt_mode_cases import CASES, CASES_BY_ID
from secret_redaction import REDACTED, redact_secrets

USER_MESSAGE = re.compile(r"<user_message>\n(.*)\n</user_message>", re.DOTALL)
PLACEHOLDER = re.compile(r"⟦URL_\d+[^⟧]*⟧")
LINKS_ERROR = "WriteWise could not keep your links intact this time. Please try again."
UNEXPECTED = "The AI service returned an unexpected response. Please try again."


class FakeResult:
    def __init__(self, text, status="completed", reason=None):
        self.output_text = text
        self.status = status
        self.incomplete_details = type("Details", (), {"reason": reason})() if reason else None


class FakeOpenAI:
    """Stands in for AsyncOpenAI. By default it 'refines' by echoing the message it was sent,
    which is enough to test everything around the model call.

    `reply` is a fixed text, a function of the message, a FakeResult, an exception, or a list
    of those used one per call (for the retry)."""

    def __init__(self):
        self.calls = []
        self.reply = None

    @property
    def responses(self):
        return self

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.reply.pop(0) if isinstance(self.reply, list) else self.reply
        if isinstance(reply, BaseException):
            raise reply
        if isinstance(reply, FakeResult):
            return reply
        message = USER_MESSAGE.search(kwargs["input"])
        message = message.group(1) if message else "Done."
        output = reply(message) if callable(reply) else (reply or message)
        return FakeResult(json.dumps({"output": output}))

    async def close(self):
        pass


@pytest.fixture
def fake(monkeypatch):
    fake_client = FakeOpenAI()
    monkeypatch.setattr(server, "openai_client", fake_client)
    return fake_client


@pytest.fixture
def client():
    return TestClient(server.app)


def refine(client, text, **extra):
    return client.post("/api/generate", json={"mode": "prompt", "input": text, **extra})


def sent_message(fake):
    return USER_MESSAGE.search(fake.calls[-1]["input"]).group(1)


SIMPLE = "make this email sound professional but not too formal"
ONE_LINK = "please check https://docs.example.com/test?id=123&source=chat and tell me if the install steps work"


# ---------- Request to OpenAI ----------

def test_prompt_mode_uses_its_own_instructions_and_the_existing_call(client, fake):
    assert refine(client, SIMPLE).status_code == 200
    call = fake.calls[-1]
    assert call["instructions"] == prompt_mode.SYSTEM_MESSAGE
    assert call["instructions"] != server.SYSTEM_MESSAGE
    assert call["model"] == server.OPENAI_MODEL
    assert call["text"] == {"format": {"type": "json_object"}}
    assert call["max_output_tokens"] == server.MAX_OUTPUT_TOKENS
    assert f"<user_message>\n{SIMPLE}\n</user_message>" in call["input"]
    assert len(fake.calls) == 1  # one model call when the links are intact


def test_system_message_keeps_the_core_rules():
    s = prompt_mode.SYSTEM_MESSAGE
    for rule in [
        "Clarify and organize. Never reinterpret.",
        "paste it into that assistant and continue the conversation",
        "Not a prompt template, and not more \"expert\" than the user",
        "Do not answer the question, give an opinion, analyze anything or perform the task.",
        "Never claim that you or anyone has opened, visited, watched, read, reviewed or verified",
        "never drop a fact just because it is background",
        "Decisions and exclusions, including negative ones",
        "What the user already tried",
        "The user's uncertainty",
        "keep only the final version",
        "Never move an instruction to the assistant into the content",
        "Add a persona or role",
        "Never summarize away details",
        "Already clear: make minimal changes.",
        "Never add generic sections such as Context, Goal, Requirements, Constraints, Expected Output",
        "A statement stays a statement, a question stays a question",
        "Never split it into a \"right?\" question tag",
        "Never expand, shorten, normalize, correct or re-capitalize them unless the user asks you to",
        "well-known names and acronyms the user typed in lowercase",
        "a command or identifier is copied character for character",
    ]:
        assert rule in s, rule


def test_response_has_only_the_refined_message(client, fake):
    fake.reply = "Make this email sound professional without making it too formal."
    data = refine(client, SIMPLE).json()
    assert data["output"] == "Make this email sound professional without making it too formal."
    assert data["mode"] == "prompt"
    assert data["variations"] is None and data["why_good_fit"] is None
    assert data["evaluation"] is None and data["detected_mode"] is None
    assert data["secrets_redacted"] is None


def test_context_profile_and_variations_are_not_used(client, fake):
    data = refine(client, "summarize this", context="CONTEXT-TEXT", experience="EXP-TEXT",
                  target_role="ROLE-TEXT", skills="SKILL-TEXT", variations=True).json()
    prompt = fake.calls[-1]["input"]
    for text in ["CONTEXT-TEXT", "EXP-TEXT", "ROLE-TEXT", "SKILL-TEXT", "User Profile"]:
        assert text not in prompt
    assert data["variations"] is None and data["output"] == "summarize this"


# ---------- Empty input ----------

@pytest.mark.parametrize("text", ["", "   ", "\n\t \n"])
def test_empty_input_never_calls_the_model(client, fake, text):
    r = refine(client, text)
    assert r.status_code == 400
    assert r.json() == {"detail": "Input text cannot be empty."}
    assert fake.calls == []


def test_too_long_input_never_calls_the_model(client, fake):
    assert refine(client, "x" * 12_001).status_code == 400
    assert fake.calls == []


# ---------- URLs ----------

@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_every_input_url_comes_back_unchanged(client, fake, case):
    assert prompt_mode.find_urls(case.input) == case.urls
    data = refine(client, case.input).json()
    for url in case.urls:
        assert url in data["output"], url
        # The model never sees the URL itself, so it cannot change it.
        assert url not in fake.calls[-1]["input"]


@pytest.mark.parametrize("url", [
    "https://example.com/test?id=123",
    "https://example.com/a%20b/c?q=x%2Fy&utm_source=news&utm_medium=email#section-2",
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "http://localhost:3000/path?x=1&y=2",
    "www.example.com/page?ref=abc",
    "https://video.example.com/watch?v=a1B2c3&t=5s",
])
def test_url_shapes_are_preserved_exactly(client, fake, url):
    fake.reply = lambda message: "Please read this. " + message
    for text in [f"read {url}", f"read {url}.", f"read ({url}) now", f"[{url}]({url})"]:
        out = refine(client, text).json()["output"]
        assert url in out, (text, out)
        assert prompt_mode.find_urls(text) == [url], text


def test_urls_survive_when_the_model_rewrites_everything_else(client, fake):
    fake.reply = lambda message: "Please check whether the install steps on this page work: " + PLACEHOLDER.search(message).group(0)
    out = refine(client, ONE_LINK).json()["output"]
    assert out == "Please check whether the install steps on this page work: https://docs.example.com/test?id=123&source=chat"


def test_same_url_twice_uses_one_placeholder():
    masked, urls = prompt_mode.mask_urls("[https://a.com/x](https://a.com/x) and https://b.com")
    assert urls == ["https://a.com/x", "https://b.com"]
    assert masked == "[⟦URL_1: a.com⟧](⟦URL_1: a.com⟧) and ⟦URL_2: b.com⟧"


def test_placeholders_show_only_the_website(client, fake):
    refine(client, CASES_BY_ID["docs_links"].input)
    message = sent_message(fake)
    assert "⟦URL_1: docs.example.com⟧" in message and "⟦URL_2: help.example.org⟧" in message
    assert "v2/setup" not in message and "utm_source" not in message
    masked, _ = prompt_mode.mask_urls("see https://user:pw@host.example.com:8080/x?y=1")
    assert masked == "see ⟦URL_1: host.example.com:8080⟧"


def test_urls_are_restored_where_the_model_put_them(client, fake):
    # Restored by number, so a reordered sentence keeps each link with what it describes.
    fake.reply = "Video: ⟦URL_2: video.example.com⟧\nGuide: ⟦URL_1⟧"
    out = refine(client, "guide https://docs.example.com/x?id=1 and video https://video.example.com/w?v=a&t=5s").json()
    assert out["output"] == "Video: https://video.example.com/w?v=a&t=5s\nGuide: https://docs.example.com/x?id=1"


def test_placeholders_with_normalised_brackets_are_restored(client, fake):
    fake.reply = "Please check [[URL_1]]."
    assert refine(client, ONE_LINK).json()["output"] == "Please check https://docs.example.com/test?id=123&source=chat."


def test_a_link_written_twice_may_come_back_once(client, fake):
    fake.reply = "Please read ⟦URL_1⟧."
    out = refine(client, "read [https://a.example.com/x](https://a.example.com/x)").json()["output"]
    assert out == "Please read https://a.example.com/x."
    assert len(fake.calls) == 1


@pytest.mark.parametrize("first_reply,problem", [
    ("Please check the install steps.", "missing ⟦URL_1⟧"),
    ("Please check ⟦URL_1⟧ and ⟦URL_1⟧.", "repeated ⟦URL_1⟧"),
    ("Please check ⟦URL_1⟧ and ⟦URL_2⟧.", "invented ⟦URL_2⟧"),
])
def test_broken_placeholders_are_retried_once(client, fake, first_reply, problem):
    fake.reply = [first_reply, "Please check whether the install steps work: ⟦URL_1⟧"]
    r = refine(client, ONE_LINK)
    assert r.status_code == 200
    assert r.json()["output"] == "Please check whether the install steps work: https://docs.example.com/test?id=123&source=chat"
    assert len(fake.calls) == 2
    retry = fake.calls[1]
    assert retry["instructions"] == prompt_mode.SYSTEM_MESSAGE
    assert f"Your previous answer was rejected: {problem}." in retry["input"]
    assert "https://docs.example.com" not in retry["input"]


def test_links_are_never_moved_or_appended_when_the_retry_also_fails(client, fake):
    fake.reply = ["Please check the install steps.", "Please check the steps."]
    r = refine(client, ONE_LINK)
    assert r.status_code == 502
    assert r.json() == {"detail": LINKS_ERROR}
    assert len(fake.calls) == 2


def test_invented_placeholder_without_links_is_retried(client, fake):
    fake.reply = ["Make this email professional. ⟦URL_7⟧", "Make this email sound professional, not too formal."]
    assert refine(client, SIMPLE).json()["output"] == "Make this email sound professional, not too formal."
    assert len(fake.calls) == 2


def test_link_problem():
    masked, _ = prompt_mode.mask_urls("a https://a.example.com b https://b.example.com")
    assert prompt_mode.link_problem("x ⟦URL_2: b.example.com⟧ y ⟦URL_1⟧", masked) is None
    assert prompt_mode.link_problem("x ⟦URL_1⟧", masked) == "missing ⟦URL_2⟧"
    assert prompt_mode.link_problem("⟦URL_1⟧ ⟦URL_1⟧ ⟦URL_2⟧ ⟦URL_3⟧", masked) == "invented ⟦URL_3⟧; repeated ⟦URL_1⟧"
    assert prompt_mode.link_problem("no links", "no links") is None


# ---------- Output validation ----------

@pytest.mark.parametrize("reply", ["", "   ", "⟦URL_1⟧"])
def test_empty_model_output_is_an_error(client, fake, reply):
    fake.reply = lambda message: reply
    r = refine(client, ONE_LINK)
    assert r.status_code == 502
    assert r.json() == {"detail": UNEXPECTED}


@pytest.mark.parametrize("model_text", [
    '{"result": "Please check this."}',
    '{"output": 42}',
    '{"output": null}',
    "not json",
    '["Please check this."]',
])
def test_malformed_model_responses_are_an_error(client, fake, model_text):
    fake.reply = FakeResult(model_text)
    r = refine(client, "check this")
    assert r.status_code == 502
    assert r.json() == {"detail": UNEXPECTED}


@pytest.mark.parametrize("wrapped", [
    "```\nPlease review this resume.\n```",
    "```text\nPlease review this resume.\n```",
    "Refined prompt: Please review this resume.",
    "Here is the refined message:\nPlease review this resume.",
    '"Please review this resume."',
    "“Please review this resume.”",
    '{"output": "Please review this resume."}',
])
def test_accidental_wrappers_are_removed(client, fake, wrapped):
    fake.reply = wrapped
    assert refine(client, "check this resume").json()["output"] == "Please review this resume."


def test_code_blocks_inside_the_message_are_kept(client, fake):
    reply = "Why does this fail?\n\n```python\nprint(x)\n```"
    fake.reply = reply
    assert refine(client, "why this fail\n```python\nprint(x)\n```").json()["output"] == reply


def test_quotes_inside_the_message_are_kept(client, fake):
    fake.reply = 'Write a message that says "see you on Monday".'
    assert refine(client, "write msg see you on monday").json()["output"] == 'Write a message that says "see you on Monday".'


def test_multiline_structure_is_kept(client, fake):
    reply = "We agreed on three points:\n1. Launch on Monday.\n2. No Excel export in this release.\n3. Mapping by Friday."
    fake.reply = reply
    assert refine(client, "meeting notes").json()["output"] == reply


def test_incomplete_response_is_not_shown(client, fake):
    fake.reply = FakeResult('{"output": "Please', status="incomplete", reason="max_output_tokens")
    assert refine(client, "check this").status_code == 422


# ---------- Errors ----------

REQUEST = httpx2.Request("POST", "https://api.openai.com/v1/responses")


@pytest.mark.parametrize("error,status", [
    (openai.RateLimitError("SECRET", response=httpx2.Response(429, request=REQUEST), body=None), 429),
    (openai.InternalServerError("SECRET", response=httpx2.Response(500, request=REQUEST), body=None), 502),
    (openai.APITimeoutError(request=REQUEST), 504),
    (openai.APIConnectionError(request=REQUEST), 503),
    (RuntimeError("SECRET internal detail"), 500),
])
def test_prompt_mode_uses_the_existing_safe_errors(client, fake, error, status):
    fake.reply = error
    r = refine(client, "check this")
    assert r.status_code == status
    assert "SECRET" not in r.text and "Traceback" not in r.text


def test_an_error_during_the_retry_is_handled_the_same_way(client, fake):
    fake.reply = ["Please check the install steps.", openai.APITimeoutError(request=REQUEST)]
    assert refine(client, ONE_LINK).status_code == 504


def test_user_text_and_links_are_not_logged(client, fake, caplog):
    caplog.set_level(logging.DEBUG)
    text = "my private note about Project Falcon https://intranet.example.com/falcon?id=9"
    fake.reply = ["No link here.", "Still no link."]
    refine(client, text)
    fake.reply = openai.APITimeoutError(request=REQUEST)
    refine(client, text)
    fake.reply = FakeResult("not json")
    refine(client, text)
    assert "Project Falcon" not in caplog.text and "intranet" not in caplog.text
    assert "retrying once: missing ⟦URL_1⟧" in caplog.text


# ---------- Secret redaction (Prompt mode only) ----------

# Built at runtime so the repository does not contain anything that looks like a real key.
FAKE_SECRETS = {
    "openai": "sk-" + "proj-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4",
    "anthropic": "sk-" + "ant-api03-" + "Zx9Yw8Vu7Ts6Rq5Po4Nm3",
    "aws": "AKIA" + "Z7QW3ER5TY2UI8OP",
    "github": "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8",
    "google": "AIza" + "SyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q",
    "slack": "xoxb-" + "1234567890-abcdefghij",
    "stripe": "sk_" + "live_" + "4eC39HqLyjWDarjtT1zdp7dc",
    "jwt": "eyJ" + "hbGciOiJIUzI1NiJ9" + ".eyJ" + "zdWIiOiIxMjM0NTY3ODkwIn0" + ".SflKxwRJSMeKKF2QT4fwpMeJf36",
}
PRIVATE_KEY = (
    "-----BEGIN " + "RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA7bq8examplekeymaterial\n"
    "abcDEF123456\n-----END " + "RSA PRIVATE KEY-----"
)
ASSIGNMENTS = {
    "OPENAI_API_KEY=abc123def456ghi789": "abc123def456ghi789",
    'password: "hunter2hunter2"': "hunter2hunter2",
    '{"client_secret": "s3cr3t-value-here"}': "s3cr3t-value-here",
    "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCY",
    "GITHUB_TOKEN: tok_9f8e7d6c5b4a": "tok_9f8e7d6c5b4a",
    "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456": "abcdefghijklmnopqrstuvwxyz123456",
}


@pytest.mark.parametrize("kind", list(FAKE_SECRETS))
def test_known_key_formats_are_redacted_before_the_model_call(client, fake, kind, caplog):
    caplog.set_level(logging.DEBUG)
    secret = FAKE_SECRETS[kind]
    data = refine(client, f"why does my deploy fail? the config uses {secret} thanks").json()
    sent = fake.calls[-1]["input"]
    assert secret not in sent
    assert REDACTED in sent
    assert data["secrets_redacted"] == 1
    assert secret not in data["output"] and REDACTED in data["output"]
    assert secret not in caplog.text and "Redacted 1 possible secret(s)" in caplog.text


def test_private_key_block_is_redacted(client, fake):
    data = refine(client, f"fix my deploy, here is the key:\n{PRIVATE_KEY}\nwhat is wrong").json()
    sent = fake.calls[-1]["input"]
    assert "examplekeymaterial" not in sent and "PRIVATE KEY" not in sent
    assert "what is wrong" in sent
    assert data["secrets_redacted"] == 1


def test_private_key_without_end_line_is_redacted_to_the_end():
    text, kinds = redact_secrets("key:\n-----BEGIN PRIVATE KEY-----\nMIIabc\nmore key material")
    assert text == f"key:\n{REDACTED}" and kinds == ["private_key"]


@pytest.mark.parametrize("text,value", list(ASSIGNMENTS.items()))
def test_secret_assignments_are_redacted(text, value):
    redacted, kinds = redact_secrets(f"here is my config {text} ok")
    assert value not in redacted
    assert REDACTED in redacted
    assert len(kinds) == 1


@pytest.mark.parametrize("text", [
    *(case.input for case in CASES),
    "The password: please reset it tomorrow.",
    "We need an API key: ask the admin team.",
    "Use max_tokens=6000 and a token budget of 500.",
    "Explain how JWT tokens and secret keys work.",
    "https://example.com/reset?token=abc123def456&id=9",
    "The sk-learn library and task-runner are fine.",
])
def test_ordinary_text_is_not_redacted(text):
    assert redact_secrets(text) == (text, [])


@pytest.mark.parametrize("mode", sorted(server.VALID_MODES - {"prompt"}))
def test_redaction_does_not_change_existing_modes(client, fake, mode):
    # Scoped to Prompt mode in V1: other modes send the request exactly as before.
    text = "config value AKIA" + "Z7QW3ER5TY2UI8OP here"
    fake.reply = FakeResult(json.dumps({"output": "Done.", "evaluation": None}))
    data = client.post("/api/generate", json={"mode": mode, "input": text}).json()
    assert text in fake.calls[-1]["input"]
    assert data["secrets_redacted"] is None


# ---------- Existing modes are unchanged ----------

@pytest.mark.parametrize("mode", sorted(server.VALID_MODES - {"prompt"}))
def test_existing_modes_still_use_the_shared_prompt(client, fake, mode):
    fake.reply = FakeResult(json.dumps({
        "detected_mode": None, "output": "Done.", "why_good_fit": None,
        "evaluation": {"clarity": 8, "professionalism": 9, "personalization": None, "suggestion": "Tip."},
    }))
    r = client.post("/api/generate", json={"mode": mode, "input": "see https://example.com/a?b=1 please"})
    assert r.status_code == 200
    data = r.json()
    assert data["output"] == "Done." and data["evaluation"]["clarity"] == 8
    assert data["secrets_redacted"] is None
    assert len(fake.calls) == 1
    call = fake.calls[-1]
    assert call["instructions"] == server.SYSTEM_MESSAGE
    assert "Task: " in call["input"] and "<user_message>" not in call["input"]
    # Existing modes still see URLs as written; only Prompt mode masks them.
    assert "https://example.com/a?b=1" in call["input"]

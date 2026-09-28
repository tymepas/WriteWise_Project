"""Live checks of model behaviour that mocked tests cannot cover (costs API credits)."""
import os
import re

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

JOB_POST = (
    "Senior Data Analyst at Northwind Health\n\nRequirements:\n"
    "- 5+ years of experience in healthcare analytics\n"
    "- Expert in SQL, Python and Tableau\n"
    "- Experience leading a team of analysts\n"
    "- Master's degree in Statistics preferred\n"
    "- AWS certification a plus\n\n"
    "We offer remote work and a collaborative team of 30 analysts."
)

# First-person claims of the posting's requirements. Only fabricated if the user did not supply them.
FABRICATED_CLAIM = re.compile(
    r"\bI (?:have|bring|possess|hold|led|lead|managed|am (?:an )?expert)\b[^.\n]*"
    r"\b(?:years|SQL|Python|Tableau|master'?s|AWS|team of analysts|healthcare analytics)\b"
    r"|\bmy (?:\d+|five|several)\+? years\b"
    r"|\bmy (?:master'?s|AWS|certification)\b",
    re.IGNORECASE,
)
PLACEHOLDER = re.compile(r"\[[^\]\n]{1,60}\]")


def generate(**body):
    r = requests.post(f"{BASE_URL}/api/generate", json=body, timeout=300)
    assert r.status_code == 200, r.text
    return r.json()


def all_text(data):
    if data.get("variations"):
        return "\n".join(v["output"] for v in data["variations"])
    return data["output"]


class TestGrounding:
    @pytest.mark.parametrize("mode,variations", [("email", False), ("email", True), ("auto", False)])
    def test_no_profile_means_no_claims_and_no_fit_bullets(self, mode, variations):
        data = generate(mode=mode, input=JOB_POST, variations=variations)
        text = all_text(data)
        assert not FABRICATED_CLAIM.search(text), FABRICATED_CLAIM.search(text).group(0)
        assert data.get("why_good_fit") is None

    def test_fit_bullets_use_only_supplied_background(self):
        data = generate(mode="email", input=JOB_POST,
                        experience="2 years as a retail sales analyst", skills="Excel")
        text = all_text(data)
        assert not FABRICATED_CLAIM.search(text), FABRICATED_CLAIM.search(text).group(0)
        bullets = data.get("why_good_fit") or []
        assert len(bullets) >= 2
        assert all(re.search(r"retail|excel|two years|2 years|sales", b, re.I) for b in bullets), bullets
        assert not any(re.search(r"\bthe user\b", b, re.I) for b in bullets), bullets

    def test_auto_still_writes_an_email_for_a_job_posting(self):
        assert generate(mode="auto", input=JOB_POST)["detected_mode"] == "email"


class TestPlaceholders:
    def test_email_without_a_name_has_no_bracket_placeholders(self):
        data = generate(mode="email", input="Write to the hiring team at Acme asking about the status of my application.")
        assert not PLACEHOLDER.search(data["output"]), data["output"]

    def test_user_written_placeholder_is_kept(self):
        data = generate(mode="grammar", input="thanks for you're help, [Your Name]")
        assert "[Your Name]" in data["output"]


TONE_TEXT = (
    "This is the third time I'm asking. Send the Q3 revenue report with all 14 regional tabs "
    "by Friday, March 6 at 5 PM, or we will miss the board deadline."
)
TONE_FACTS = {
    "request count": r"\bthird\b|\b3rd\b|three times",
    "14 tabs": r"\b14\b|fourteen",
    "Q3": r"\bQ3\b|third quarter",
    "Friday": r"Friday",
    "March 6": r"March 6",
    "5 PM": r"\b5(?::00)?\s?(?:PM|p\.m\.)",
    "board deadline": r"board",
}


class TestToneFacts:
    @pytest.mark.parametrize("tone", ["professional", "casual", "friendly", "diplomatic",
                                      "formal", "confident", "persuasive", "empathetic"])
    def test_tone_keeps_every_fact(self, tone):
        out = generate(mode="tone", input=TONE_TEXT, tone=tone)["output"]
        missing = [name for name, pattern in TONE_FACTS.items() if not re.search(pattern, out, re.I)]
        assert not missing, f"{tone} lost {missing}: {out}"


REWRITE_DRAFT = (
    "Honestly I think we kinda need to rethink the onboarding thing. So basically a lot of new users are "
    "dropping off at the payment step, like around 40% of them last month, which is a lot, and I feel like "
    "if we just made the pricing page clearer and maybe added a free trial it would probably help a bunch. "
    "Could we talk about this at Thursday's planning meeting?"
)


class TestRewriteGoals:
    def test_all_goals_work_keep_facts_and_differ(self):
        goals = ["clear_concise", "more_direct", "more_polished", "more_persuasive", "simplify", "keep_style"]
        outputs = {g: generate(mode="rewrite", input=REWRITE_DRAFT, rewrite_goal=g)["output"] for g in goals}
        for goal, out in outputs.items():
            assert "40" in out and "Thursday" in out, f"{goal} lost a fact: {out}"
        assert len(set(outputs.values())) == len(goals)

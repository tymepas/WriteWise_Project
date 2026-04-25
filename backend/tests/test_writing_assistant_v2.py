"""Backend tests for enhanced AI Writing Assistant - iteration 2"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAutoMode:
    """Auto mode detection tests"""

    def test_auto_mode_grammar_detection(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "auto",
            "input": "I has went to the store and buyed many things their.",
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("detected_mode") is not None
        assert data["mode"] == "auto"
        # Should detect grammar mode
        assert data.get("detected_mode") == "grammar"
        assert data.get("output") is not None

    def test_auto_mode_email_detection(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "auto",
            "input": "Software Engineer at Google\nRequirements:\n- 5 years Python\n- Experience with ML\n- Strong communication skills",
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("detected_mode") == "email"
        assert data.get("output") is not None


class TestVariations:
    """Variations feature tests"""

    def test_variations_returns_3_cards(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "email",
            "input": "I want to apply for the Software Engineer position at Acme Corp.",
            "variations": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("variations") is not None
        assert len(data["variations"]) == 3
        labels = [v["label"] for v in data["variations"]]
        assert "Professional" in labels
        assert "Confident" in labels
        assert "Friendly" in labels

    def test_variations_each_has_output(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "email",
            "input": "Applying for product manager role at startup",
            "variations": True,
        })
        assert r.status_code == 200
        data = r.json()
        for v in data["variations"]:
            assert "label" in v
            assert "output" in v
            assert len(v["output"]) > 0

    def test_no_variations_returns_single_output(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "email",
            "input": "I want to apply for a software engineering position",
            "variations": False,
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("output") is not None
        assert data.get("variations") is None


class TestWhyGoodFit:
    """Why Good Fit section tests"""

    def test_email_mode_job_posting_returns_why_good_fit(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "email",
            "input": """Senior Software Engineer at TechCorp
Requirements:
- 5+ years Python/Django experience
- Experience with distributed systems
- Strong communication skills
About: We build developer tools used by 50,000 teams.""",
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("why_good_fit") is not None
        assert isinstance(data["why_good_fit"], list)
        assert len(data["why_good_fit"]) >= 2

    def test_grammar_mode_no_why_good_fit(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "grammar",
            "input": "I has went to the interview and it was went well.",
        })
        assert r.status_code == 200
        data = r.json()
        # why_good_fit should be None for grammar mode
        assert data.get("why_good_fit") is None


class TestEvaluation:
    """Evaluation scores tests"""

    def test_evaluation_scores_present(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "email",
            "input": "I want to apply for a software engineering role",
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("evaluation") is not None
        ev = data["evaluation"]
        assert "clarity" in ev
        assert "professionalism" in ev
        assert "personalization" in ev
        assert "suggestion" in ev
        assert 1 <= ev["clarity"] <= 10
        assert 1 <= ev["professionalism"] <= 10
        assert 1 <= ev["personalization"] <= 10

    def test_personalization_score_higher_with_profile(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "email",
            "input": "Applying for Senior React Developer at TechCorp",
            "experience": "5 years React developer",
            "target_role": "Senior React Developer",
            "skills": "React, TypeScript, Node.js",
        })
        assert r.status_code == 200
        data = r.json()
        ev = data.get("evaluation")
        assert ev is not None
        # With profile, personalization score should be >= 7
        assert ev["personalization"] >= 7


class TestValidation:
    """Input validation tests"""

    def test_empty_input_400(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={"mode": "grammar", "input": ""})
        assert r.status_code == 400

    def test_whitespace_only_input_400(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={"mode": "grammar", "input": "   "})
        assert r.status_code == 400

    def test_invalid_mode_400(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={"mode": "unknown", "input": "some text"})
        assert r.status_code == 400

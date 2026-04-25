"""
WriteWise v3 backend tests - new modes: paraphrase, summarize, expand, shorten, humanize
Also validates: invalid mode, empty input, variations toggle behavior
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

SAMPLE_TEXT = (
    "Artificial intelligence is transforming the way businesses operate. "
    "Companies are using AI to automate repetitive tasks, improve customer service, "
    "and gain insights from large datasets. This technology is no longer limited to "
    "large corporations. Small businesses are also adopting AI tools to stay competitive."
)


class TestNewModes:
    """Tests for paraphrase, summarize, expand, shorten, humanize modes"""

    def test_paraphrase_standard(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "paraphrase",
            "input": SAMPLE_TEXT,
            "paraphrase_mode": "standard"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in paraphrase standard"
        assert data["mode"] == "paraphrase"

    def test_paraphrase_simple(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "paraphrase",
            "input": SAMPLE_TEXT,
            "paraphrase_mode": "simple"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in paraphrase simple"

    def test_paraphrase_creative(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "paraphrase",
            "input": SAMPLE_TEXT,
            "paraphrase_mode": "creative"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in paraphrase creative"

    def test_paraphrase_formal(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "paraphrase",
            "input": SAMPLE_TEXT,
            "paraphrase_mode": "formal"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in paraphrase formal"

    def test_paraphrase_fluency(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "paraphrase",
            "input": SAMPLE_TEXT,
            "paraphrase_mode": "fluency"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in paraphrase fluency"

    def test_summarize_short(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "summarize",
            "input": SAMPLE_TEXT,
            "summary_type": "short"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in summarize short"
        assert data["mode"] == "summarize"

    def test_summarize_bullets(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "summarize",
            "input": SAMPLE_TEXT,
            "summary_type": "bullets"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in summarize bullets"
        output = data["output"]
        # Bullets should start with dashes
        lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
        has_bullets = any(l.startswith('-') for l in lines)
        assert has_bullets, f"Bullet output should have lines starting with '-'. Got: {output[:300]}"

    def test_expand(self):
        short_text = "AI helps businesses grow faster by automating tasks."
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "expand",
            "input": short_text
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in expand mode"
        # Expanded output should be longer
        assert len(data["output"]) > len(short_text), "Expanded output should be longer than input"

    def test_shorten(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "shorten",
            "input": SAMPLE_TEXT
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in shorten mode"
        # Shortened output should be shorter
        assert len(data["output"]) < len(SAMPLE_TEXT), "Shortened output should be shorter than input"

    def test_humanize(self):
        robotic_text = (
            "The implementation of artificial intelligence technologies facilitates "
            "operational efficiency optimization and resource allocation enhancement "
            "within corporate organizational frameworks."
        )
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "humanize",
            "input": robotic_text
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("output"), "Expected output in humanize mode"


class TestValidation:
    """Validation tests: invalid mode, empty input"""

    def test_invalid_mode(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "invalid_mode",
            "input": "some text"
        })
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"

    def test_empty_input(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "grammar",
            "input": ""
        })
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"

    def test_whitespace_input(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "grammar",
            "input": "   "
        })
        assert resp.status_code == 400, f"Expected 400 for whitespace input"


class TestNoEmDashes:
    """Verify no em dashes or double hyphens in outputs"""

    def test_email_no_em_dashes(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "email",
            "input": "Software Engineer position at TechCorp. 5 years experience Python."
        })
        assert resp.status_code == 200
        output = resp.json().get("output", "")
        assert "—" not in output, f"Em dash found in email output: {output[:300]}"
        assert " -- " not in output, f"Double hyphen found in email output: {output[:300]}"

    def test_paraphrase_no_em_dashes(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "paraphrase",
            "input": SAMPLE_TEXT,
            "paraphrase_mode": "standard"
        })
        assert resp.status_code == 200
        output = resp.json().get("output", "")
        assert "—" not in output, f"Em dash found in paraphrase output"


class TestDetectedModeIsolation:
    """detected_mode should only be returned for auto mode"""

    def test_auto_mode_detected_mode_present(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "auto",
            "input": "Please fix this sentense, it has errrors."
        })
        assert resp.status_code == 200
        data = resp.json()
        # detected_mode may or may not be present but should be accessible
        assert "detected_mode" in data

    def test_non_auto_mode_no_detected_mode(self):
        resp = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "grammar",
            "input": "This sentense has errrors."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("detected_mode") is None, "detected_mode should be null for non-auto modes"

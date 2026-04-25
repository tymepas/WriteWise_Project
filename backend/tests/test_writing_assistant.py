import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndRoot:
    def test_root_returns_message(self):
        r = requests.get(f"{BASE_URL}/api/")
        assert r.status_code == 200
        data = r.json()
        assert "message" in data

class TestGenerateEndpoint:
    def test_grammar_mode(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "grammar",
            "input": "I has a problem with my grammer",
        })
        assert r.status_code == 200
        data = r.json()
        assert "output" in data
        assert data["mode"] == "grammar"
        assert len(data["output"]) > 0

    def test_email_mode_returns_subject(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "email",
            "input": "Software engineer job posting at TechCorp, need 3 years React experience",
        })
        assert r.status_code == 200
        data = r.json()
        assert "output" in data
        assert data["mode"] == "email"
        assert "Subject:" in data["output"]

    def test_tone_mode(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "tone",
            "input": "hey can you send me that report asap",
            "context": "formal"
        })
        assert r.status_code == 200
        data = r.json()
        assert "output" in data
        assert data["mode"] == "tone"

    def test_rewrite_mode(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "rewrite",
            "input": "The thing is that i think we should maybe consider looking at the possibility of doing things differently",
        })
        assert r.status_code == 200
        data = r.json()
        assert "output" in data
        assert data["mode"] == "rewrite"

    def test_empty_input_returns_400(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "grammar",
            "input": "   ",
        })
        assert r.status_code == 400

    def test_invalid_mode_returns_400(self):
        r = requests.post(f"{BASE_URL}/api/generate", json={
            "mode": "invalid_mode",
            "input": "some text",
        })
        assert r.status_code == 400

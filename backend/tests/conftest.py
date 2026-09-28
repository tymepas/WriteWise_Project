import os
import sys
from pathlib import Path

# Mocked tests must never use a real key. Set a fake one before server.py loads
# backend/.env (python-dotenv does not override variables that already exist).
os.environ["OPENAI_API_KEY"] = "test-key-not-real"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

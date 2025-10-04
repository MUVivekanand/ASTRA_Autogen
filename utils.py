# utils.py
import json
from pathlib import Path

TOKEN_FILE = Path(".token.json")


def is_authenticated() -> bool:
    """Check if user is authenticated by verifying token file"""
    if not TOKEN_FILE.exists():
        return False

    try:
        data = json.loads(TOKEN_FILE.read_text())
        if "token" in data:
            return True
    except Exception:
        return False

    return False
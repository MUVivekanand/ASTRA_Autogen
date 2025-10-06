import requests
from utils.check import is_authenticated

def check_with_opa(prompt: str) -> bool:
    """Send prompt to OPA and get allow/deny decision"""
    input_data = {
        "input": {
            "prompt": prompt,
            "is_authenticated": is_authenticated()
        }
    }
    try:
        resp = requests.post("http://localhost:8181/v1/data/prompt/allow", json=input_data)
        resp.raise_for_status()
        decision = resp.json()
        return decision.get("result", False)
    except Exception as e:
        print(f"OPA check failed: {e}")
        return False
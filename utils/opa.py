import requests
from utils.check import is_authenticated
from utils.check import get_authenticated_user_info
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

def check_with_opa(tool: str) -> bool:
    """
    Send the canonical tool + user info to OPA and get allow/deny decision.
    """
    mongo_client = MongoClient(MONGO_URI)
    role = ""

    try:
        if not is_authenticated():
            print("User not authenticated")
            return False

        user_info = get_authenticated_user_info()
        email = user_info.get("email")
        print(f"User email from token: {email}")

        if not email:
            print("No email found in user info")
            return False

        db = mongo_client["test"]
        users = db["users"]
        user_doc = users.find_one({"email_id": email})
        if not user_doc:
            print(f"No user found in DB with email_id: {email}")
            return False

        role = user_doc.get("role", "")
        print(f"User role: {role}")

        input_data = {
            "input": {
                "is_authenticated": True,
                "role": role,
                "tool": tool
            }
        }

        print(f"\nSending to OPA: {input_data}")
        resp = requests.post(
            "http://localhost:8181/v1/data/mcp_tools/allow",
            json=input_data,
            timeout=5
        )
        resp.raise_for_status()
        decision = resp.json()
        allowed = decision.get("result", False)
        print(f"OPA Decision: {'ALLOWED' if allowed else 'DENIED'}")
        return allowed

    except Exception as e:
        print(f"OPA check failed: {e}")
        return False
    finally:
        mongo_client.close()
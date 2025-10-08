import requests
from utils.check import is_authenticated
from utils.check import get_authenticated_user_info
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

def check_with_opa(prompt: str) -> bool:
    """Send prompt to OPA and get allow/deny decision"""
    mongo_client = MongoClient(MONGO_URI)
    email = None
    role = ""

    db = mongo_client["test"]
    users = db["users"]  

    print("=" * 50)
    print("Starting OPA check...")

    if is_authenticated():
        user = get_authenticated_user_info()

        email = user.get('email')
        print(f"Email extracted from token: '{email}'")

        if email:
            user_doc = users.find_one({"email_id": email})

            if user_doc:
                if "role" in user_doc:
                    role = user_doc["role"]
                    print(f"Role extracted: '{role}'")
                else:
                    print(f"No 'role' field found in user document")
            else:
                print(f"No user found in database with email_id: '{email}'")
        else:
            print("No email found in user info")
    else:
        print("User is not authenticated")

    input_data = {
        "input": {
            "prompt": prompt,
            "is_authenticated": is_authenticated(),
            "role": role if role else ""
        }
    }

    try:
        resp = requests.post("http://localhost:8181/v1/data/prompt/allow", json=input_data)
        resp.raise_for_status()
        decision = resp.json()
        print(f"\nOPA Response: {decision}")
        result = decision.get("result", False)
        return result
    except Exception as e:
        print(f"\nOPA check failed: {e}")
        return False
    finally:
        mongo_client.close()
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
    role = ""  # Default to empty string instead of None

    db = mongo_client["test"]
    users = db["users"]  

    print("=" * 50)
    print("Starting OPA check...")
    print(f"Is authenticated: {is_authenticated()}")

    if is_authenticated():
        user = get_authenticated_user_info()
        print(f"User info from token: {user}")

        email = user.get('email')
        print(f"Email extracted from token: '{email}'")

        if email:
            # Query using email_id instead of email
            print(f"\nQuerying MongoDB for email_id: '{email}'")
            user_doc = users.find_one({"email_id": email})  # Changed from "email" to "email_id"
            print(f"User document found: {user_doc}")

            if user_doc:
                print(f"✓ User document found!")
                print(f"All fields in document: {list(user_doc.keys())}")

                if "role" in user_doc:
                    role = user_doc["role"]
                    print(f"✓ Role extracted: '{role}'")
                else:
                    print(f"✗ No 'role' field found in user document")
            else:
                print(f"✗ No user found in database with email_id: '{email}'")
        else:
            print("✗ No email found in user info")
    else:
        print("✗ User is not authenticated")

    input_data = {
        "input": {
            "prompt": prompt,
            "is_authenticated": is_authenticated(),
            "role": role if role else ""
        }
    }

    print(f"\nFinal values being sent to OPA:")
    print(f"  - is_authenticated: {is_authenticated()}")
    print(f"  - role: '{role}'")
    print(f"  - prompt: '{prompt[:50]}...' (truncated)")
    print("=" * 50)

    try:
        resp = requests.post("http://localhost:8181/v1/data/prompt/allow", json=input_data)
        resp.raise_for_status()
        decision = resp.json()
        print(f"\nOPA Response: {decision}")
        result = decision.get("result", False)
        print(f"OPA Decision: {'ALLOWED ✓' if result else 'DENIED ✗'}")
        return result
    except Exception as e:
        print(f"\n✗ OPA check failed: {e}")
        return False
    finally:
        mongo_client.close()
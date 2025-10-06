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
    is_admin = False

    db = mongo_client["test"]
    users = db["users"]  

    if is_authenticated():
        user = get_authenticated_user_info()
        email = user['email']
        if email:
            user_doc = users.find_one({"email": email})
            if user_doc and "is_admin" in user_doc:
                is_admin = user_doc["is_admin"]

    input_data = {
        "input": {
            "prompt": prompt,
            "is_authenticated": is_authenticated(),
            "is_admin": is_admin
        }
    }
    print(is_authenticated(), is_admin)
    
    try:
        resp = requests.post("http://localhost:8181/v1/data/prompt/allow", json=input_data)
        resp.raise_for_status()
        decision = resp.json()
        return decision.get("result", False)
    except Exception as e:
        print(f"OPA check failed: {e}")
        return False

check_with_opa("Sridev")
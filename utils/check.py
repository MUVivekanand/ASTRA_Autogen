import json
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['openid', 'profile', 'email']
TOKEN_FILE = Path(__file__).parent.parent / ".token.json"

def verify_token_integrity() -> bool:
    if not os.path.exists(TOKEN_FILE):
        return False
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except (json.JSONDecodeError, ValueError, KeyError):
        return False
    
    if not creds.token:
        return False
    
    try:
        if creds.expired and creds.refresh_token:
            print("Token expired, attempting refresh...")
            creds.refresh(Request())
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print("Token refreshed successfully")
        
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        
        if not user_info.get('id') or not user_info.get('email'):
            return False
        
        print(f"Token verified for user: {user_info.get('email')}")
        return True
        
    except HttpError:
        return False
    
    except Exception:
        return False

def is_authenticated() -> bool:
    return verify_token_integrity()

def get_authenticated_user_info():
    if not os.path.exists(TOKEN_FILE):
        return None
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds.token:
            return None
        
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        
        return user_info
        
    except Exception:
        return None

# if __name__ == "__main__":
#     print("Checking MCP authorization...")
    
#     if is_authenticated():
#         print("✅ User is authenticated")
#         print("🔓 Activating MCP tools...")
#         user = get_authenticated_user_info()
#         if user:
#             print(f"   Authenticated as: {user['email']}")
#             print(f"   Name: {user.get('name', 'N/A')}")
        
#     else:
#         print("❌ User is NOT authenticated")
#         print("🔒 MCP tools remain disabled")
#         print("   Please complete OAuth authentication first")
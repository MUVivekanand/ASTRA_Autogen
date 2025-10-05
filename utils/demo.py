import json
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['openid', 'profile', 'email']
TOKEN_FILE = Path(__file__).parent.parent / ".token.json"

class TokenVerificationError(Exception):
    """Raised when token verification fails"""
    pass

def verify_token_integrity():
    """
    Verifies that the token in .token.json is a valid Google OAuth token.
    This prevents bypass attacks where users put placeholder values.
    
    Returns:
        dict: User info if token is valid
    Raises:
        TokenVerificationError: If token is invalid or verification fails
    """
    
    if not os.path.exists(TOKEN_FILE):
        raise TokenVerificationError("Token file not found. User needs to authenticate.")
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        raise TokenVerificationError(f"Invalid token file format: {e}")
    
    if not creds.token:
        raise TokenVerificationError("Token is missing or empty")
    
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
            raise TokenVerificationError("Token validation returned incomplete user data")
        
        print(f"✅ Token verified for user: {user_info.get('email')}")
        return user_info
        
    except HttpError as e:
        error_details = e.error_details[0] if e.error_details else {}
        reason = error_details.get('reason', 'unknown')
        raise TokenVerificationError(f"Google API rejected token: {reason} - {e}")
    
    except Exception as e:
        raise TokenVerificationError(f"Token verification failed: {e}")


def is_user_authenticated():
    """
    Simple check if user is authenticated with valid token.
    Use this before activating MCP tools.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        verify_token_integrity()
        return True
    except TokenVerificationError as e:
        print(f"❌ Authentication failed: {e}")
        return False


def get_authenticated_user_info():
    """
    Get verified user information.
    Use this to check WHO is authenticated.
    
    Returns:
        dict: User info (id, email, name, picture) or None if not authenticated
    """
    try:
        return verify_token_integrity()
    except TokenVerificationError:
        return None

if __name__ == "__main__":
    print("Checking MCP authorization...")
    
    if is_user_authenticated():
        print("✅ User is authenticated")
        print("🔓 Activating MCP tools...")
        user = get_authenticated_user_info()
        print(f"   Authenticated as: {user['email']}")
        print(f"   Name: {user.get('name', 'N/A')}")
        
    else:
        print("❌ User is NOT authenticated")
        print("🔒 MCP tools remain disabled")
        print("   Please complete OAuth authentication first")
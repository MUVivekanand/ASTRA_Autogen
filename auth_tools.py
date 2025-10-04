import os
from pathlib import Path
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import webbrowser
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(name = "simple-mcp")

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
TOKEN_FILE = Path(__file__).parent / ".token.json"

#as scopes is required
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

creds = None
if TOKEN_FILE.exists() and TOKEN_FILE.stat().st_size > 0:
    try:
        token_data = json.loads(TOKEN_FILE.read_text())
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    except json.JSONDecodeError:
        print(".token.json is empty or invalid. Please re-authenticate.")


@mcp.tool()
async def authenticate() -> str:
    """Authenticate with Google OAuth to access other tools"""
    global creds

    if creds and creds.valid:
        return "Already authenticated"

    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

    try:
        webbrowser.open(auth_url)
        browser_opened = True
    except:
        browser_opened = False

    message = f"Please visit this URL to authorize the application:\n{auth_url}\n\n"
    if browser_opened:
        message += "Your browser should open automatically. "

    message += "After authorization, copy the authorization code from the page and use the 'complete_auth' tool with the code."

    return message


@mcp.tool()
async def complete_auth(authorization_code: str) -> str:
    """Complete OAuth authentication with the authorization code"""
    global creds

    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    try:
        flow.fetch_token(code=authorization_code)
        creds = flow.credentials

        TOKEN_FILE.write_text(creds.to_json())

        return "Authentication successful! Credentials saved."
    except Exception as e:
        return f"Authentication failed: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
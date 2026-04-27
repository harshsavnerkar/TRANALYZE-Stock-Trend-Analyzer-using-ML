import os
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501"

def get_google_auth_url():
    """Build the URL for the Google Sign-In screen."""
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
        redirect_uri=REDIRECT_URI
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

def verify_google_token(token):
    """Verify the token returned by Google and get user info."""
    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        return id_info
    except Exception as e:
        print(f"Token Verification Failed: {e}")
        return None

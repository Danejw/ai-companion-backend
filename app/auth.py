import os
import requests
from fastapi import HTTPException, Security, WebSocket, WebSocketException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from jose import jwt, JWTError
from app.utils.user_context import current_user_id
import base64
from typing import Optional


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1/user"

# HTTP
security = HTTPBearer()

# Websocket
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

# If the key is base64 encoded, decode it
if SECRET_KEY.startswith("base64:"):
    SECRET_KEY = base64.b64decode(SECRET_KEY[7:])

ALGORITHM = "HS256"  # or whatever you prefer



def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Uses Supabase's built-in authentication API to verify the user's JWT token.
    """
    token = credentials.credentials
    logging.info(f"🔍 Verifying Token: {token[:20]}... (truncated)")  # Avoid printing full token

    # Verify with Supabase API (instead of manually decoding)
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY
    }
    response = requests.get(SUPABASE_AUTH_URL, headers=headers)

    logging.info(f"🔍 Supabase Verification Status: {response.status_code}, Response: {response.json()}")

    if response.status_code != 200:
        error_detail = {"error": "UNAUTHENTICATED"}
        raise HTTPException(
            status_code=401,
            detail=error_detail
        )

    user_data = response.json()
    
    # Store the user id in the context
    current_user_id.set(user_data["id"])
    
    return user_data  # Return the user details


async def verify_token_websocket(token: str) -> Optional[dict]:
    try:
        # Get Supabase JWT public key
        jwks_url = "https://azcltjyvrttwdznrdfgab.supabase.co/auth/v1/jwks"
        jwks = requests.get(jwks_url).json()
        
        # Get the key ID from the token header
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header["kid"]
        
        # Find the matching public key
        public_key = None
        for key in jwks["keys"]:
            if key["kid"] == key_id:
                public_key = key
                break
                
        if not public_key:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            
        # Verify the token using Supabase's public key
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="authenticated"
        )
        return payload
        
    except Exception as e:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")

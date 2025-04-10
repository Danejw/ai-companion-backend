import os
import requests
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1/user"

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    ✅ Uses Supabase's built-in authentication API to verify the user's JWT token.
    """
    token = credentials.credentials
    logging.info(f"🔍 Verifying Token: {token[:20]}... (truncated)")  # Avoid printing full token

    # 🔥 Verify with Supabase API (instead of manually decoding)
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY
    }
    response = requests.get(SUPABASE_AUTH_URL, headers=headers)

    logging.info(f"🔍 Supabase Verification Status: {response.status_code}, Response: {response.json()}")

    if response.status_code != 200:
        error_detail = {"error": "NOT_AUTHENTICATED"}
        raise HTTPException(
            status_code=401,
            detail=error_detail
        )

    user_data = response.json()
    
    return user_data  # ✅ Return the user details

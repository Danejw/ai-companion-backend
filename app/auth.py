import os
import requests
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1/user"

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    ✅ Uses Supabase's built-in authentication API to verify the user's JWT token.
    """
    token = credentials.credentials
    print(f"🔍 Verifying Token: {token[:20]}... (truncated)")  # Avoid printing full token

    # 🔥 Verify with Supabase API (instead of manually decoding)
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_KEY
    }
    response = requests.get(SUPABASE_AUTH_URL, headers=headers)

    print(f"🔍 Supabase Verification Status: {response.status_code}, Response: {response.json()}")

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_data = response.json()
    print(f"✅ User Verified: {user_data}")
    
    return user_data  # ✅ Return the user details

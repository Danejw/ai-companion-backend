import os
import requests
from fastapi import HTTPException, Security, WebSocket, WebSocketException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from jose import jwt, JWTError

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_AUTH_URL = f"{SUPABASE_URL}/auth/v1/user"

# HTTP
security = HTTPBearer()

# Websocket
SECRET_KEY = os.getenv("SUPABASE_JWT_SECRET") # match whatever you use for generating tokens
ALGORITHM = "HS256"  # or whatever you prefer



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
        error_detail = {"error": "UNAUTHENTICATED"}
        raise HTTPException(
            status_code=401,
            detail=error_detail
        )

    user_data = response.json()
    
    return user_data  # ✅ Return the user details


async def verify_token_websocket(websocket: WebSocket):
    #await websocket.accept()
    
    token = websocket.query_params.get("token")
    if not token:
        # Policy violation: no token found
        
        #await websocket.send_json({"type": "error", "text": "UNAUTHENTICATED"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="authenticated")
        user_id: str = payload.get("sub")
        
        #await websocket.send_json({"type": "info", "text": "AUTHENTICATED"})
        
        if user_id is None:
            #await websocket.send_json({"type": "error", "text": "UNAUTHENTICATED"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")

        # If everything checks out, return the user_id
        return user_id

    except JWTError:
        # Token is invalid or expired
        #await websocket.send_json({"type": "error", "text": "UNAUTHENTICATED"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")

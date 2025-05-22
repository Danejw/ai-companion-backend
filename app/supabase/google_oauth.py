import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def sign_in_with_google_id_token(id_token: str):
    """Exchange a Google ID token for a Supabase session."""
    response = supabase.auth.sign_in_with_id_token({
        "provider": "google",
        "id_token": id_token,
    })
    return response

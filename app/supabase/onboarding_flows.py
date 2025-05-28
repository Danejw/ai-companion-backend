import logging
import os
from typing import Dict, Optional
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


class OnboardingRepository:
    def __init__(self) -> None:
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        self.table_name = "user_onboarding_flows"

    def upsert_onboarding_flow(self, user_id: str) -> None:
        """Insert default onboarding flow for a user if it doesn't exist."""
        default_flow = {
            "status": "in_progress",
            "last_screen": None,
            "responses": {},
            "screen_order": [
                "welcome",
                "name",
                "vibe_check",
                "intent",
                "time_commitment",
                "role_preference",
                "growth_interest",
                "voice_preference",
                "personal_touch",
                "orientation",
            ],
        }
        try:
            self.supabase.table(self.table_name).upsert(
                {"user_id": user_id, "flow": default_flow}, on_conflict="user_id"
            ).execute()
        except Exception as e:  # pragma: no cover - supabase interaction
            logging.error(
                f"Error upserting onboarding flow for user {user_id}: {e}")

    def get_flow(self, user_id: str) -> Optional[Dict]:
        """Retrieve the onboarding flow for a user."""
        try:
            response = (
                self.supabase.table(self.table_name)
                .select("flow")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            return response.data.get("flow") if response.data else None
        except Exception as e:  # pragma: no cover - supabase interaction
            logging.error(f"Error fetching onboarding flow for {user_id}: {e}")
            return None

    def update_flow(self, user_id: str, flow: Dict) -> None:
        """Update a user's onboarding flow."""
        try:
            self.supabase.table(self.table_name).update({"flow": flow}).eq(
                "user_id", user_id
            ).execute()
        except Exception as e:  # pragma: no cover - supabase interaction
            logging.error(f"Error updating onboarding flow for {user_id}: {e}")


import logging
import os
from typing import List, Optional
from pydantic import BaseModel
from supabase import create_client, Client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


class UserFeedback(BaseModel):
    user_id: str
    context: str
    feedback: str
    sentiment: str

class UserFeedbackRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        self.table_name = "user_feedback"

    def create_user_feedback(self, user_feedback: UserFeedback) -> bool:
        try:
            self.supabase.table(self.table_name).insert(user_feedback.model_dump()).execute()
            return True
        except Exception as e:
            logging.error(f"Error creating user feedback: {e}")
            raise

    def get_user_feedback(self, user_id: str) -> Optional[List[UserFeedback]]:
        try:    
            response = self.supabase.table(self.table_name).select("*").eq("user_id", user_id).execute()
            return response.data
        except Exception as e:
            logging.error(f"Error fetching user feedback for user_id: {user_id}: {e}")
            return None



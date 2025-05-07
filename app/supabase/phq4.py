import os
import logging
from typing import Literal, Optional
from uuid import UUID
from supabase import create_client, Client
from pydantic import BaseModel, Field


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class Phq4Questionaire(BaseModel):
    user_id: Optional[UUID] = None
    stage: Literal['pre', 'post']
    q1: int = Field(..., ge=0, le=3)
    q2: int = Field(..., ge=0, le=3)
    q3: int = Field(..., ge=0, le=3)
    q4: int = Field(..., ge=0, le=3)
    phq4_score: int = Field(..., ge=0, le=12)

    class Config:
        orm_mode = True


class Phq4Repository:
    """
    Repository class responsible for all Supabase CRUD PHQ4 table operations
    """
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        self.table_name = "phq4_questionaires"

    def create_phq4(self, phq4: Phq4Questionaire):
        try:
            self.supabase.table(self.table_name).insert(phq4.model_dump()).execute()
        except Exception as e:
            logging.error(f"Error creating PHQ4 for user {phq4.user_id}: {e}")

    def get_phq4(self, user_id: str):
        try:
            # check if user id has at least 1 response
            response = self.supabase.table(self.table_name).select("*").eq("user_id", user_id).execute()
            if len(response.data) > 0:
                return response.data
            else:
                return []
        except Exception as e:
            logging.error(f"Error getting PHQ4 for user {user_id}: {e}")
            return []
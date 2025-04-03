import os
import logging
from typing import Optional
from supabase import create_client, Client
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class MBTI(BaseModel):
    extraversion_introversion: float = 0.0
    sensing_intuition: float = 0.0
    thinking_feeling: float = 0.0
    judging_perceiving: float = 0.0
    message_count: int = 0
    


class MBTIRepository:
    """
    Repository class responsible for all Supabase read/write operations
    for the MBTI data.
    """
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.table_name = "mbti_personality"  # Update if needed

    def get_mbti(self, user_id: str) -> Optional[MBTI]:
        """
        Retrieves the MBTI record for a specific user from Supabase.
        If none exists, creates a new default record and returns it.
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("user_id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                record = data[0]
                return MBTI(**record)
            else:
                logging.info(f"No MBTI record found for user_id: {user_id}. Creating a new one.")
                # Create a default MBTI record; ensure your MBTI model has default values set
                new_mbti = MBTI()  # This uses defaults defined in your MBTI model
                new_mbti_data = new_mbti.dict()
                new_mbti_data["user_id"] = user_id
                
                insert_response = self.supabase.table(self.table_name).insert(new_mbti_data).execute()
                if insert_response.data and len(insert_response.data) > 0:
                    record = insert_response.data[0]
                    return MBTI(**record)
                else:
                    logging.error(f"Failed to create MBTI record for user {user_id}.")
                    return None
        except Exception as e:
            logging.error(f"Error fetching MBTI data for user {user_id}: {e}")
            return None

    def upsert_mbti(self, user_id: str, mbti: MBTI) -> None:
        """
        Inserts or updates (upserts) the MBTI record for a specific user.
        """
        record_dict = mbti.dict()
        record_dict["user_id"] = user_id
        try:
            # Check if record already exists
            existing = self.supabase.table(self.table_name).select("*").eq("user_id", user_id).execute()
            if existing.data and len(existing.data) > 0:
                # Update
                self.supabase.table(self.table_name).update(record_dict).eq("user_id", user_id).execute()
                logging.info(f"Updated MBTI record for user_id: {user_id}")
            else:
                # Insert
                self.supabase.table(self.table_name).insert(record_dict).execute()
                logging.info(f"Inserted new MBTI record for user_id: {user_id}")
        except Exception as e:
            logging.error(f"Error upserting MBTI data for user {user_id}: {e}")

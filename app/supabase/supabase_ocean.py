import os
import logging
from typing import Optional
from supabase import create_client, Client
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class Ocean(BaseModel):
    openness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    agreeableness: float = 0.0
    neuroticism: float = 0.0
    response_count: int = 0

class OceanResponse(BaseModel):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

class OceanRepository:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.table_name = "ocean_personality"

    def get_ocean(self, user_id: str) -> Optional[Ocean]:
        """
        Get the OCEAN record for a user. If no record exists, create a new one.
        """
        try:
            # Try to retrieve the OCEAN record for the user
            response = self.supabase.table(self.table_name).select("*").eq("user_id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                record = data[0]
                return Ocean(**record)
            else:
                logging.info(f"No OCEAN record found for user_id: {user_id}. Creating a new one.")
                # Create a default OCEAN object; ensure your Ocean model has default values set.
                new_ocean = Ocean()  # assumes defaults, e.g., all zeros and response_count=0
                # Include the user_id in the inserted record:
                new_ocean_data = new_ocean.dict()
                new_ocean_data["user_id"] = user_id
                
                # Insert the new record into Supabase
                insert_response = self.supabase.table(self.table_name).insert(new_ocean_data).execute()
                if insert_response.data and len(insert_response.data) > 0:
                    record = insert_response.data[0]
                    return Ocean(**record)
                else:
                    logging.error(f"Failed to create OCEAN record for user {user_id}.")
                    return None
        except Exception as e:
            logging.error(f"Error fetching OCEAN data for user {user_id}: {e}")
            return None

    def upsert_ocean(self, user_id: str, ocean: Ocean) -> None:
        record_dict = ocean.dict()
        record_dict["user_id"] = user_id
        try:
            existing = self.supabase.table(self.table_name).select("*").eq("user_id", user_id).execute()
            if existing.data and len(existing.data) > 0:
                self.supabase.table(self.table_name).update(record_dict).eq("user_id", user_id).execute()
                logging.info(f"Updated OCEAN record for user_id: {user_id}")
            else:
                self.supabase.table(self.table_name).insert(record_dict).execute()
                logging.info(f"Inserted new OCEAN record for user_id: {user_id}")
        except Exception as e:
            logging.error(f"Error upserting OCEAN data for user {user_id}: {e}")

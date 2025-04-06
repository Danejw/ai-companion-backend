import os
import logging
from typing import Optional
from supabase import create_client, Client
from pydantic import BaseModel


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class Profile(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    image: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    subscription: Optional[str] = None
    credits: Optional[int] = None
    birthdate: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    credits_used: Optional[int] = None


class ProfileRepository:
    """
    Repository class responsible for all Supabase CRUD operations
    for the profiles table.
    """
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        self.table_name = "profiles"

    def get_user_email(self, user_id: str) -> Optional[str]:
        """
        Retrieves the email from the profile record in Supabase.
        Returns the email or None if no record is found.
        """
        try:    
            response = self.supabase.table(self.table_name).select("email").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["email"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching email for user_id: {user_id}: {e}")
            return None
        
    def get_user_name(self, user_id: str) -> Optional[str]:
        """
        Retrieves the name from the profile record in Supabase.
        Returns the name or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("name").eq("id", user_id).execute()
            data = response.data    
            if data and len(data) > 0:
                return data[0]["name"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching name for user_id: {user_id}: {e}")
            return None
        
    def get_user_image(self, user_id: str) -> Optional[str]:
        """
        Retrieves the image from the profile record in Supabase.
        Returns the image or None if no record is found.    
        """
        try:
            response = self.supabase.table(self.table_name).select("image").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["image"]     
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching image for user_id: {user_id}: {e}")
            return None
        
    def update_user_name(self, user_id: str, name: str) -> bool:
        """
        Updates the name of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"name": name}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating name for user_id: {user_id}: {e}")
            return False
        
    def update_user_image(self, user_id: str, image: str) -> bool:
        """
        Updates the image of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"image": image}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating image for user_id: {user_id}: {e}")
            return False

    def get_user_subscription(self, user_id: str) -> Optional[str]:
        """
        Retrieves the subscription from the profile record in Supabase.
        Returns the subscription or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("subscription").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["subscription"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching subscription for user_id: {user_id}: {e}")
            return None
        
    def update_user_subscription(self, user_id: str, subscription: str) -> bool:
        """
        Updates the subscription of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"subscription": subscription}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating subscription for user_id: {user_id}: {e}")
            return False
        
    def get_user_credit(self, user_id: str) -> Optional[int]:
        """         
        Retrieves the credit from the profile record in Supabase.
        Returns the credit or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("credits").eq("id", user_id).execute()
            data = response.data    
            if data and len(data) > 0:
                return data[0]["credits"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching credits for user_id: {user_id}: {e}")
            return None
        
    def update_user_credit(self, user_id: str, credit: int) -> bool:
        """
        Updates the credits of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"credits": credit}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating credits for user_id: {user_id}: {e}")
            return False    
            
    def deduct_credits(self, user_id: str, amount: int) -> bool:
        """Atomically deduct credits from user's balance"""
        try:
            # make sure the amount is positive
            if amount < 0:
                logging.error(f"Amount to deduct is negative for user {user_id}")
                return False
            
            current_credits = self.get_user_credit(user_id)
            
            if current_credits is None or current_credits < amount:
                logging.error(f"Insufficient credits for user {user_id}")
                return False
            
            new_credits = current_credits - amount
 
            credits = self.supabase.table(self.table_name).update({"credits": new_credits}).eq("id", user_id).execute()
            credits_used = self.supabase.table(self.table_name).update({"credits_used": amount}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Failed to deduct credits for user {user_id}: {e}")
            return False

    def get_user_credits_used(self, user_id: str) -> Optional[int]:
        """
        Retrieves the credits used from the profile record in Supabase.
        Returns the credits used or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("credits_used").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["credits_used"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching credits used for user_id: {user_id}: {e}")
            return None
    
    def get_profile(self, user_id: str) -> Optional[Profile]:
        """
        Retrieves the profile record for a specific user from Supabase.
        Returns a Profile object or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                record = data[0]
                return Profile(**record)
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching profile data for user {user_id}: {e}")
            return None
        
    def increment_user_credit(self, user_id: str, additional_credits: int):
        # This should increment the user's credits by the given amount.
        # Implement according to your Supabase client usage.
        try:
            # make sure the amount is positive
            if additional_credits < 0:
                logging.error(f"Amount to increment is negative for user {user_id}")
                return False
            
            # Retrieve the current credits (example using a synchronous call)
            current = self.get_user_credit(user_id)
            new_total = current + additional_credits
            response = self.supabase.table("profiles").update({"credits": new_total}).eq("id", user_id).execute()
            return self.get_user_credit(user_id)
        except Exception as e:
            logging.error(f"Failed to increment credits for user {user_id}: {e}")
            raise

    def get_user_birthdate(self, user_id: str) -> Optional[str]:
        """
        Retrieves the birthdate from the profile record in Supabase.
        Returns the birthdate or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("birthdate").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["birthdate"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching birthdate for user_id: {user_id}: {e}")
            return None

    def update_user_birthdate(self, user_id: str, birthdate: str) -> bool:
        """
        Updates the birthdate of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"birthdate": birthdate}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating birthdate for user_id: {user_id}: {e}")
            return False

    def get_user_location(self, user_id: str) -> Optional[str]:
        """
        Retrieves the location from the profile record in Supabase.
        Returns the location or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("location").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["location"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching location for user_id: {user_id}: {e}")
            return None

    def update_user_location(self, user_id: str, location: str) -> bool:
        """
        Updates the location of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"location": location}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating location for user_id: {user_id}: {e}")
            return False

    def get_user_gender(self, user_id: str) -> Optional[str]:
        """
        Retrieves the gender from the profile record in Supabase.
        Returns the gender or None if no record is found.
        """
        try:
            response = self.supabase.table(self.table_name).select("gender").eq("id", user_id).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["gender"]
            else:
                logging.info(f"No profile record found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error fetching gender for user_id: {user_id}: {e}")
            return None
        
    def update_user_gender(self, user_id: str, gender: str) -> bool:
        """
        Updates the gender of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"gender": gender}).eq("id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error updating gender for user_id: {user_id}: {e}")
            return False










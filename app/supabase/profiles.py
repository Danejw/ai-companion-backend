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
        
    def update_user_name(self, user_id: str, name: str) -> str:
        """
        Updates the name of the user in the profile record in Supabase.
        Returns True if update was successful, False otherwise.
        """
        try:
            response = self.supabase.table(self.table_name).update({"name": name}).eq("id", user_id).execute()
            return "Name updated successfully"
        except Exception as e:
            logging.error(f"Error updating name for user_id: {user_id}: {e}")
            return "Error updating name"
           
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
            current_credits_used = self.get_user_credits_used(user_id)
            
            if current_credits is None or current_credits < amount:
                logging.error(f"Insufficient credits for user {user_id}")
                return False
            
            deducted_credits = current_credits - amount
            new_used_credits = current_credits_used + amount
            
 
            credits = self.supabase.table(self.table_name).update({"credits": deducted_credits}).eq("id", user_id).execute()
            credits_used = self.supabase.table(self.table_name).update({"credits_used": new_used_credits}).eq("id", user_id).execute()
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

    def complete_account_deletion(self, user_id: str) -> dict:
        """
        Completely deletes a user account from Supabase following best practices:
        1. Check for and handle storage objects
        2. Revoke all active sessions
        3. Delete auth record (which cascades to all related tables)
        
        Returns status information about the deletion process.
        """
        results = {
            "success": True,
            "storage_cleared": False,
            "sessions_revoked": False,
            "auth_deleted": False,
            "message": ""
        }
        
        try:
            # Step 1: Check for storage objects owned by the user
            # TODO: Implement this when we use storage
            # try:
            #     # List storage objects owned by user
            #     storage_objects = self.supabase.storage.from_('your-bucket-name').list(user_id)
                
            #     # If objects exist, delete them or handle accordingly
            #     if storage_objects and len(storage_objects) > 0:
            #         for obj in storage_objects:
            #             self.supabase.storage.from_('your-bucket-name').remove([f"{user_id}/{obj['name']}"])
                
            #     results["storage_cleared"] = True
            # except Exception as e:
            #     logging.warning(f"Error handling storage objects for user {user_id}: {e}")
            
            # Step 2: Revoke all active sessions
            try:
                # Update all sessions to be revoked
                self.supabase.rpc(
                    "revoke_sessions_for_user",
                    {"input_user_id": user_id}
                ).execute()
                results["sessions_revoked"] = True
            except Exception as e:
                logging.warning(f"Failed to revoke sessions for user {user_id}: {e}")
            
            # Step 3: Delete auth record using admin API
            # This will cascade to profiles and all other tables with CASCADE constraints
            auth_deleted = self.supabase.auth.admin.delete_user(user_id)
            results["auth_deleted"] = True
            
            results["message"] = "User account completely deleted"
            return results
            
        except Exception as e:
            error_msg = f"Error during complete account deletion for user_id {user_id}: {e}"
            logging.error(error_msg)
            results["success"] = False
            results["message"] = error_msg
            return results

    def send_password_reset(self, email: str) -> dict:
        """
        Sends a password reset email to the user.
        Returns a dictionary with the status of the operation.
        
        This uses the Supabase Auth API to send a magic link for password reset.
        """
        try:
            # Send password reset email
            response = self.supabase.auth.reset_password_for_email(
                email, 
                options={
                    # Optionally specify a redirect URL where user will land after clicking the link
                    # This URL needs to be added to your allowed redirect URLs in Supabase dashboard
                    "redirect_to": "http://localhost:3000/reset-password"
                }
            )
            
            return {
                "success": True,
                "message": "Password reset email sent successfully"
            }
        except Exception as e:
            error_msg = f"Error sending password reset email to {email}: {e}"
            return {
                "success": False,
                "message": error_msg
            }

    def update_user_password(self, user_id: str, new_password: str) -> dict:
        """
        Updates a user's password in Supabase Auth.
        
        This method should be called by an authenticated endpoint after
        verifying the user's identity (either after reset flow or when
        user wants to change password while logged in).
        
        Args:
            user_id: The ID of the user whose password to update
            new_password: The new password to set
            
        Returns:
            Dictionary with success status and message
        """
        try:
            # Update the user's password using admin API
            response = self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password}
            )
            
            logging.info(f"Password updated successfully for user: {user_id}")
            return {
                "success": True,
                "message": "Password updated successfully"
            }
        except Exception as e:
            error_msg = f"Error updating password for user {user_id}: {e}"
            logging.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }





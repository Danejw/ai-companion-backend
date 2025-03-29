import logging
import os
from typing import Dict
from openai import OpenAI


api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


class ModerationService:
    """Service class for handling OpenAI content moderation"""
    
    def __init__(self):
        pass

    def check_content(self, text: str) -> Dict:
        """
        Check if content violates OpenAI's content policy
        
        Args:
            text (str): The text content to moderate
            
        Returns:
            Dict containing:
                flagged (bool): Whether the content was flagged
                categories (dict): Specific categories that were flagged
                scores (dict): Confidence scores for each category
                error (str, optional): Error message if request failed
        """

        try:
            # Make the API call
            moderation = client.moderations.create(input=text)

            # Check if results are present
            if not moderation.results:
                logging.warning("Moderation API returned empty results list for input.")
                return None # Or handle as appropriate

            # Get the first result object (this is an OpenAI Pydantic model)
            result = moderation.results[0]

            # Convert the result object to a dictionary for simple return
            result_dict = result.model_dump()

            return result_dict

        except Exception as e: # Catch unexpected errors
            logging.error(f"An unexpected error occurred during moderation: {type(e).__name__} - {e}")
            return None
            
    def check_image(self, image_url: str) -> Dict:
        """
        Check if an image violates OpenAI's content policy
        """
        try:
                        # Convert HttpUrl to string if needed
            image_url_str = str(image_url)
            
            moderation = client.moderations.create(
            model="omni-moderation-latest",
            input=[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url_str,
                            # can also use base64 encoded image URLs
                            # "url": "data:image/jpeg;base64,abcdefg..."
                        }
                    },
                ],
            )

            result = moderation.results[0]
            result_dict = result.model_dump()
            
            logging.info(f"Moderation result: {result_dict}")
            return result_dict
        
        except Exception as e:
            logging.error(f"Moderation API request failed: {str(e)}")
            return False

    def is_safe(self, text: str = None, image_url: str = None) -> bool:
        """
        Simple helper that returns True if content is safe, False otherwise
        
        Args:
            text (str): The text content to moderate
            
        Returns:
            bool: True if content is safe, False if flagged or error occurred
        """
        
        content_flagged = False
        if text and text.strip() != "": 
            content_result = self.check_content(text)
            content_flagged = content_result["flagged"]
            
        image_flagged = False
        if image_url and image_url.strip() != "": 
            image_result = self.check_image(image_url)
            image_flagged = image_result["flagged"]
            
        # only return true if both content and image are false
        if content_flagged or image_flagged:
            return False
        else:
            return True
        
        
# Tools
#region Description
import logging
from agents import function_tool
from fastapi import HTTPException
from app.personal_agents.knowledge_extraction import KnowledgeExtractionService
from app.supabase.conversation_history import clear_conversation_history
from app.supabase.profiles import ProfileRepository
from app.supabase.user_feedback import UserFeedback, UserFeedbackRepository
from app.utils.user_context import current_user_id

profile_repo = ProfileRepository()
user_feedback_repo = UserFeedbackRepository()


@function_tool
def get_users_name() -> str:
    """
    Retrieves the name of the user from the profile repository.
    
    Returns:
    - str: the name of the user
    """ 
    user_id = current_user_id.get()
    return profile_repo.get_user_name(user_id)


@function_tool
def get_user_birthdate() -> str:
    """
    Retrieves the birthdate of the user from the profile repository.

    Returns:
    - datetime.date: the birthdate of the user
    """
    user_id = current_user_id.get()
    return profile_repo.get_user_birthdate(user_id)


@function_tool
def get_user_location() -> str:
    """
    Retrieves the location of the user from the profile repository.
    
    Returns:
    - str: the location of the user
    """
    user_id = current_user_id.get()
    return profile_repo.get_user_location(user_id)


@function_tool
def get_user_gender() -> str:
    """
    Retrieves the gender of the user from the profile repository.
    
    Returns:
    - str: the gender of the user
    """
    user_id = current_user_id.get()
    return profile_repo.get_user_gender(user_id)


@function_tool
def update_user_name(name: str) -> bool:
    """
    Updates the user's name in the profile repository.

    Parameters:
    - name (str): The new name to update for the user.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """ 
    user_id = current_user_id.get()
    print(f"Updating user name to: {user_id} {name}")
    return profile_repo.update_user_name(user_id, name)


@function_tool
def update_user_birthdate(birthdate: str) -> bool:
    """
    Updates the user's birthdate in the profile repository.
    
    Parameters:
    - birthdate (datetime.date): The new birthdate to update for the user.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """
    user_id = current_user_id.get()
    return profile_repo.update_user_birthdate(user_id, birthdate)


@function_tool
def update_user_location(location: str) -> bool:
    """
    Updates the user's location in the profile repository.
    
    Parameters:
    - location (str): The new location to update for the user.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """
    user_id = current_user_id.get()
    return profile_repo.update_user_location(user_id, location)


@function_tool
def update_user_gender(gender: str) -> bool:
    """
    Updates the user's gender in the profile repository.    
    
    Parameters:
    - gender (str): The new gender to update for the user.

    Returns:
    - bool: True if the update was successful, False otherwise.
    """
    user_id = current_user_id.get()
    return profile_repo.update_user_gender(user_id, gender)


@function_tool
async def retrieve_personalized_info_about_user(query: str) -> str:
    """
    Retireve personalized information about the user for more personalized, deeper, and meaningful conversation.
    
    - query (str): The query to find addtional information about the user to personalize the conversation.

    Returns:
    - str: the addtional information about the user
    """
    user_id = current_user_id.get()
    knowledge_service = KnowledgeExtractionService(user_id)
    try:
        return await knowledge_service.retrieve_similar_knowledge(query)
    except Exception as e:
        logging.error(f"Error retrieving knowledge: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@function_tool
async def create_user_feedback(user_feedback: UserFeedback) -> str:
    """
    Creates user feedback and stores it in the database
    
    Parameters:
    - user_feedback (UserFeedback): The user feedback to create.
        class UserFeedback(BaseModel):
            user_id: str   # The unique identifier of the user.
            context: str  # The Summary of the conversation history leading up to the user's message.
            feedback: str  # The feedback of the user.
            sentiment: str  # The sentiment of the user feedback.

    Returns:
    - bool: True if the user feedback was created successfully, False otherwise.
    """
    user_id = current_user_id.get()
    user_feedback.user_id = user_id
    return user_feedback_repo.create_user_feedback(user_feedback)


@function_tool
def clear_history():
    """
    Clears the history for the user.
    """
    user_id = current_user_id.get()
    return clear_conversation_history(user_id)

#endregion
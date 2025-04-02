import logging
from fastapi import APIRouter, HTTPException, status
from app.auth import verify_token
from fastapi.params import Depends
from app.supabase.pgvector import get_user_knowledge_vectors, get_user_slang_vectors, remove_user_knowledge, remove_user_slang
from fastapi.responses import JSONResponse


# Initialize the router
router = APIRouter()


@router.get("/get-knowledge-vectors")
async def get_user_credits_route(limit: int = 10, user_id=Depends(verify_token)):
    """
    Retrieves a list of vectors for a specific user.
    """
    try:
        user_id = user_id["id"]
        vectors = get_user_knowledge_vectors(user_id, limit)        
        
        # Build a response with the id, text, and last_updated fields
        response = []
        for vector in vectors:
            response.append({
                "id": vector["id"],
                "text": vector["knowledge_text"],
                "last_updated": vector["last_updated"],
                "mentions": vector["mention_count"]
            })    
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while retrieving vectors for user {user_id}: {str(e)}"
        )
        

@router.get("/get-slang-vectors")
async def get_user_slang_vectors_route(limit: int = 10, user_id=Depends(verify_token)):
    """
    Retrieves a list of slang vectors for a specific user.
    """
    try:
        user_id = user_id["id"]
        vectors = get_user_slang_vectors(user_id, limit)
                
        # Build a response with the id, text, and last_updated fields
        response = []
        for vector in vectors:
            response.append({
                "id": vector["id"],
                "text": vector["slang_text"],
                "last_updated": vector["last_updated"],
                "mentions": vector["mention_count"]
            })    
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while retrieving slang vectors for user {user_id}: {str(e)}"
        )


@router.delete("/remove-knowledge-vector")
async def remove_user_knowledge_vector(knowledge_id: str, user_id=Depends(verify_token)):
    """
    Removes a knowledge vector for a specific user.
    """
    try:
        user_id = user_id["id"]
        result = remove_user_knowledge(user_id, knowledge_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while removing knowledge vector for user {user_id}: {str(e)}"
        )


@router.delete("/remove-slang-vector")
async def remove_user_slang_vector(slang_id: str, user_id=Depends(verify_token)):
    """
    Removes a slang vector for a specific user.
    """
    try:
        user_id = user_id["id"]
        result = remove_user_slang(user_id, slang_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while removing slang vector for user {user_id}: {str(e)}"
        )





from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from app.auth import verify_token
from app.function.notifications import PushSubscription, ScheduleTask, get_vapid_public_key, schedule_push_notification, subscribe_push_notification, unsubscribe_push_notification

router = APIRouter()

@router.get("/vapid-public")
async def get_vapid_key():
    key = get_vapid_public_key()
    return {"vapidPublicKey": key}

@router.post("/subscribe")
async def subscribe(subscription: PushSubscription, user: str = Depends(verify_token)):
    try:
        user_id = user["id"]              
        response = subscribe_push_notification(user_id, subscription)
        return {"status": "ok", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/schedule")
async def schedule_task(task: ScheduleTask, user: str = Depends(verify_token)):
    try:    
        user_id = user["id"]
        
        response = schedule_push_notification(user_id, task)
             
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="No push subscription found for user.")
        
        return {"status": "scheduled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        

@router.delete("/unsubscribe")
async def unsubscribe(user: str = Depends(verify_token)):
    try:
        user_id = user["id"]
        response = unsubscribe_push_notification(user_id)
        return {"status": "unsubscribed", "deleted": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



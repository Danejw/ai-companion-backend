from datetime import datetime, timezone
import logging
from dateutil import parser
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
from pywebpush import webpush, WebPushException
import os
from supabase import create_client, Client

from app.auth import verify_token
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


router = APIRouter()

executors = {'default': ThreadPoolExecutor(5)}

scheduler = BackgroundScheduler(executors=executors)


VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIMS = {"sub": "mailto:your_email@example.com"}

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict

class ScheduleTask(BaseModel):
    title: str
    body: str
    send_at: str  # ISO8601 datetime (e.g., "2025-04-18T10:30:00")

def start_scheduler_once():
    if not scheduler.running:
        scheduler.start()
    else:
        logging.info("⚠️ [Scheduler] Already running. Skipping startup.")      

def send_push(subscription_dict, title, body):
    try:
        payload = json.dumps({ "title": title, "body": body })

        webpush(
            subscription_info=subscription_dict,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS,
        )


    except WebPushException as ex:
        logging.error(f"Error sending push notification: {ex}")
    except Exception as e:
        print("🔥 Unexpected error:", e)

@router.get("/vapid-public")
async def get_vapid_public_key():
    return {"vapidPublicKey": VAPID_PUBLIC_KEY}

@router.post("/subscribe")
async def subscribe(subscription: PushSubscription, user: str = Depends(verify_token)):
    try:
        user_id = user["id"]
                
        response = supabase.table("push_subscriptions").upsert({
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "user_id": user_id
        }, on_conflict=["user_id"]).execute()

        return {"status": "ok", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/schedule")
async def schedule_task(task: ScheduleTask, user: str = Depends(verify_token)):
    try:
        user_id = user["id"]
        
        send_time = parser.isoparse(task.send_at).astimezone(timezone.utc)

        # now = datetime.now(timezone.utc)  # 🔁 Force UTC
        # diff_seconds = int((send_time - now).total_seconds())

        # print("--------------------------------")
        # print("📝 Notification Scheduled (UTC)")
        # print("📍 Created at:", now.strftime("%B %d, %I:%M:%S %p"))
        # print("📅 Scheduled for:", send_time.strftime("%B %d, %I:%M:%S %p"))
        # print(f"⏳ This event is scheduled in {diff_seconds} seconds")
        # print("--------------------------------")

        response = supabase.table("push_subscriptions").select("*").eq("user_id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="No push subscription found for user.")
        
        first_sub = response.data[0]
        subscription_data = {
            "endpoint": first_sub["endpoint"],
            "keys": first_sub["keys"]
        }

         
        scheduler.add_job(
            send_push,
            "date",
            run_date=send_time,
            args=[subscription_data, task.title, task.body]
        )
        
        return {"status": "scheduled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/unsubscribe")
async def unsubscribe(user: str = Depends(verify_token)):
    try:
        user_id = user["id"]

        response = supabase.table("push_subscriptions").delete().eq("user_id", user_id).execute()

        print(f"🗑️ Unsubscribed user: {user_id}")
        return {"status": "unsubscribed", "deleted": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

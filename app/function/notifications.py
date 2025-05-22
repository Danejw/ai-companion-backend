

import os
import json
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from dotenv import load_dotenv
from pywebpush import webpush, WebPushException
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timezone
import logging
from dateutil import parser


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict

class ScheduleTask(BaseModel):
    title: str
    body: str
    send_at: str 
    recurrence: Optional[str] = None  # e.g., "daily", "weekly", "monthly"



VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIMS = {"sub": "mailto:your_email@example.com"}


load_dotenv(override=True)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


executors = {'default': ThreadPoolExecutor(5)}
scheduler = BackgroundScheduler(executors=executors)


def get_vapid_public_key() -> str:
    return VAPID_PUBLIC_KEY

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

def subscribe_push_notification(user_id: str, subscription: PushSubscription):
    return supabase.table("push_subscriptions").upsert({
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "user_id": user_id
        }, on_conflict=["user_id"]).execute()

def schedule_push_notification(user_id: str, task: ScheduleTask):
    send_time = parser.isoparse(task.send_at).astimezone(timezone.utc)
    
    now = datetime.now(timezone.utc)  # 🔁 Force UTC
    diff_seconds = int((send_time - now).total_seconds())

    print("--------------------------------")
    print("📝 Notification Scheduled (UTC)")
    print("📍 Created at:", now.strftime("%B %d, %Y, %I:%M:%S %p"))
    print("📅 Scheduled for:", send_time.strftime("%B %d, %Y, %I:%M:%S %p"))
    print(f"⏳ This event is scheduled in {diff_seconds} seconds")
    print("--------------------------------")

    response = supabase.table("push_subscriptions").select("*").eq("user_id", user_id).execute()
    
    # automatically subscribe to push notifications if the user has no subscriptions
    if len(response.data) == 0:
        return {"error": "No push subscription found for user. You need to subscribe to push notifications first."}
    
    first_sub = response.data[0]
    subscription_data = {
        "endpoint": first_sub["endpoint"],
        "keys": first_sub["keys"]
    }
 
 
    if task.recurrence:
        if task.recurrence == "one-time":
            scheduler.add_job(
                send_push,
                trigger="date",
                run_date=send_time,
                args=[subscription_data, task.title, task.body]
            ) 
        elif task.recurrence == "daily":
            scheduler.add_job(
                send_push,
                trigger="cron",
                hour=send_time.hour,
                minute=send_time.minute,
                args=[subscription_data, task.title, task.body],
                id=f"daily-{user_id}-{task.title}",
                replace_existing=True
            )
        elif task.recurrence == "weekly":
            scheduler.add_job(
                send_push,
                trigger="cron",
                day_of_week=send_time.weekday(),
                hour=send_time.hour,
                minute=send_time.minute,
                args=[subscription_data, task.title, task.body],
                id=f"weekly-{user_id}-{task.title}",
                replace_existing=True
            )
        elif task.recurrence == "monthly":
            scheduler.add_job(
                send_push,
                trigger="cron",
                day=send_time.day,
                hour=send_time.hour,
                minute=send_time.minute,
                args=[subscription_data, task.title, task.body],
                id=f"monthly-{user_id}-{task.title}",
                replace_existing=True
            )
    else:
        scheduler.add_job(
            send_push,
            trigger="date",
            run_date=send_time,
            args=[subscription_data, task.title, task.body]
        )

    return response

def unsubscribe_push_notification(user_id: str):
    return supabase.table("push_subscriptions").delete().eq("user_id", user_id).execute()

from agents import Agent, function_tool
from app.function.notifications import ScheduleTask, schedule_push_notification, unsubscribe_push_notification
from app.utils.user_context import current_user_id
import dateparser

#region Tools
@function_tool
def schedule_a_push_notification(task: ScheduleTask, relative_time: str):
    """
    Schedule a push notification for a user

    Args:
        task (ScheduleTask): the task to schedule the push notification
        relative_time (str): plain text describing when to send the push notification (e.g. "at 10:00 AM on Monday or in an hour")
    
    ScheduleTask Schema:
    {
        "title": "string", # the short title of the push notification
        "body": "string", # the body of the push notification
        "send_at": "string", # plain text describing when to send the push notification (e.g. "at 10:00 AM on Monday or in an hour")
        "recurrence": "string" # "one-time", "daily", "weekly", "monthly"
    }
    """
    # Convert relative string like "in 3 minutes" or "tomorrow at 5pm"
    dt= dateparser.parse(relative_time, settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True})
    if not dt:
        raise ValueError("Could not parse relative time string")
    
    task.send_at = dt.isoformat()
    
    user_id = current_user_id.get()
    return schedule_push_notification(user_id, task)

@function_tool
def unsubscribe_from_push_notification():
    """
    Unsubscribe from push notifications for a user

    Args:
        user_id (str): the user id of the user to unsubscribe from push notifications
    """
    user_id = current_user_id.get()
    return unsubscribe_push_notification(user_id)
#endregion


instruction = """
You are a notification agent that can schedule and unschedule push notifications.

You can use the following tools to perform the actions:
- schedule_a_push_notification
- unsubscribe_from_push_notification

When scheduling a push notification, you can use the relative time to schedule the push notification. 
The relative time is a plain text describing when to send the push notification 
e.g. "at 10:00 AM on Monday" or "in an hour"
"""

notification_agent = Agent(
    name="Notification Agent",
    handoff_description="The Notification Agent that can schedule push notifications, and unsubscribe from push notifications.",
    instructions=instruction,
    tools=[schedule_a_push_notification, unsubscribe_from_push_notification],
)



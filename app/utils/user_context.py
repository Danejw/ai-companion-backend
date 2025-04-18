# app/utils/user_context.py
from contextvars import ContextVar

# Store the current user id in the context
current_user_id: ContextVar[str] = ContextVar("current_user_id", default=None)

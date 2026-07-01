import contextvars

# Context variables to hold the active request's user ID and channel ID
current_user_id = contextvars.ContextVar("current_user_id", default=None)
current_channel_id = contextvars.ContextVar("current_channel_id", default=None)

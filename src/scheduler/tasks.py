"""
Task Scheduler Module

This module provides task scheduling capabilities using APScheduler.
Users can set reminders and schedule messages to be sent at specific times.

Features:
- One-time reminders
- Recurring tasks (using cron expressions)
- Task persistence in database
- LangChain-compatible tools
"""

from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from langchain.tools import tool

from src.utils.logger import get_logger
from src.database import get_db_session, ScheduledTask
from src.config import config

logger = get_logger(__name__)

# Global scheduler
scheduler: AsyncIOScheduler | None = None
slack_client = None


def set_slack_client(client):
    """
    Set the Slack client for sending scheduled messages.
    
    Args:
        client: Slack Web API client
    """
    global slack_client
    slack_client = client


async def execute_scheduled_task(task_id: str):
    """
    Execute a scheduled task.
    
    This function is called by APScheduler when a task is due.
    
    Args:
        task_id: Task ID from database
    """
    try:
        with get_db_session() as db:
            task = db.query(ScheduledTask).filter(
                ScheduledTask.task_id == task_id
            ).first()
            
            if not task or not task.is_active:
                logger.warning(f"Task {task_id} not found or inactive")
                return
            
            # Send message
            if slack_client:
                await slack_client.chat_postMessage(
                    channel=task.channel_id,
                    text=f"⏰ Reminder: {task.message}"
                )
                logger.info(f"Executed task {task_id}: {task.message[:50]}...")
            
            # Update last run
            task.last_run = datetime.utcnow()
            
            # If not recurring, mark as inactive
            if not task.is_recurring:
                task.is_active = False
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}", exc_info=True)


def initialize_scheduler() -> AsyncIOScheduler:
    """
    Initialize the APScheduler instance.
    
    This function:
    1. Creates the scheduler
    2. Loads existing tasks from database
    3. Schedules them
    4. Starts the scheduler
    
    Returns:
        AsyncIOScheduler: Initialized scheduler
    """
    global scheduler
    
    logger.info("Initializing task scheduler...")
    
    # Create scheduler
    scheduler = AsyncIOScheduler()
    
    # Load existing tasks from database
    try:
        with get_db_session() as db:
            active_tasks = db.query(ScheduledTask).filter(
                ScheduledTask.is_active == True
            ).all()
            
            for task in active_tasks:
                # Schedule based on task type
                if task.is_recurring and task.cron_expression:
                    # Recurring task with cron
                    trigger = CronTrigger.from_crontab(task.cron_expression)
                elif task.schedule_time:
                    # One-time task
                    trigger = DateTrigger(run_date=task.schedule_time)
                else:
                    logger.warning(f"Task {task.task_id} has no valid schedule")
                    continue
                
                scheduler.add_job(
                    execute_scheduled_task,
                    trigger=trigger,
                    args=[task.task_id],
                    id=task.task_id,
                    replace_existing=True
                )
            
            logger.info(f"Loaded {len(active_tasks)} scheduled tasks")
    
    except Exception as e:
        logger.error(f"Error loading tasks: {e}", exc_info=True)
    
    # Start scheduler
    scheduler.start()
    logger.info("✅ Task scheduler initialized")
    
    return scheduler


# LangChain Tools

@tool
async def set_reminder(
    user_id: str,
    channel_id: str,
    message: str,
    when: str
) -> str:
    """
    Set a reminder to be sent at a specific time.
    
    Use this tool when users ask to be reminded about something.
    
    Args:
        user_id: Slack user ID
        channel_id: Slack channel ID where reminder should be sent
        message: Reminder message
        when: When to send the reminder (e.g., "tomorrow at 10am", "in 2 hours")
        
    Returns:
        str: Confirmation message
        
    Example:
        >>> await set_reminder("U123456", "C789012", "Review the PR", "tomorrow at 10am")
        "✅ Reminder set for tomorrow at 10:00 AM"
    """
    try:
        # Parse "when" string into datetime
        # This is a simplified implementation
        # Full implementation would use dateparser or similar
        
        schedule_time = None
        
        if "tomorrow" in when.lower():
            schedule_time = datetime.now() + timedelta(days=1)
            # TODO: Parse time from "when" string
        elif "in" in when.lower():
            # Parse relative time (e.g., "in 2 hours")
            # TODO: Implement relative time parsing
            pass
        
        if not schedule_time:
            return "⚠️ Could not parse time. Please use format like 'tomorrow at 10am' or 'in 2 hours'"
        
        # Create task in database
        task_id = f"reminder_{user_id}_{datetime.now().timestamp()}"
        
        with get_db_session() as db:
            task = ScheduledTask(
                task_id=task_id,
                user_id=user_id,
                channel_id=channel_id,
                task_type="reminder",
                message=message,
                schedule_time=schedule_time,
                is_recurring=False
            )
            db.add(task)
            db.commit()
        
        # Schedule with APScheduler
        if scheduler:
            scheduler.add_job(
                execute_scheduled_task,
                trigger=DateTrigger(run_date=schedule_time),
                args=[task_id],
                id=task_id,
                replace_existing=True
            )
        
        logger.info(f"Set reminder for {schedule_time}: {message}")
        return f"✅ Reminder set for {schedule_time.strftime('%Y-%m-%d %H:%M')}"
        
    except Exception as e:
        logger.error(f"Error setting reminder: {e}", exc_info=True)
        return f"Error setting reminder: {str(e)}"


@tool
async def schedule_message(
    channel_id: str,
    message: str,
    when: str,
    recurring: bool = False
) -> str:
    """
    Schedule a message to be sent at a specific time.
    
    Use this tool when users want to schedule a message for later.
    
    Args:
        channel_id: Slack channel ID
        message: Message to send
        when: When to send (e.g., "every day at 9am", "next Monday at 2pm")
        recurring: Whether this is a recurring message
        
    Returns:
        str: Confirmation message
        
    Example:
        >>> await schedule_message("C789012", "Daily standup reminder", "every day at 9am", True)
        "✅ Message scheduled to send every day at 9:00 AM"
    """
    logger.info(f"Schedule message requested: {message[:50]}... at {when}")
    return "⚠️ Message scheduling not fully implemented yet. Use set_reminder for one-time reminders."


# Export tools
SCHEDULER_TOOLS = [
    set_reminder,
    schedule_message,
]


if __name__ == "__main__":
    # Test scheduler
    import asyncio
    
    async def test():
        sched = initialize_scheduler()
        print(f"Scheduler running: {sched.running}")
    
    asyncio.run(test())

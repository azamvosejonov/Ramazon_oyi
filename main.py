import asyncio
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import admin_command, user_data, save_user_data, start, button, handle_message
from scheduler import schedule_daily_tasks, init_scheduler
import threading

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING,  # Only show warnings and above by default
    handlers=[
        logging.StreamHandler()
    ]
)

# Disable verbose logging for httpx and apscheduler
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Our main logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global flag to track if scheduler is running
scheduler_running = False

def run_scheduler():
    """Run the scheduler in a separate thread"""
    global scheduler_running
    if not scheduler_running:
        scheduler_running = True
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Import here to avoid circular imports
            from handlers import user_data
            
            # Initialize and start the scheduler
            scheduler = init_scheduler()
            
            # Run the tasks in the same event loop
            async def run_tasks():
                await schedule_daily_tasks(user_data)
                scheduler.start(paused=False)
                
            loop.run_until_complete(run_tasks())
            loop.run_forever()
            
        except Exception as e:
            logger.error(f"Error in scheduler: {e}", exc_info=True)
        finally:
            scheduler_running = False
            if 'loop' in locals():
                loop.close()

if __name__ == "__main__":
    from config import BOT_TOKEN

    try:
        # Initialize bot
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .build()
        )

        # Add handlers with proper grouping
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CommandHandler('admin', admin_command))
        application.add_handler(CallbackQueryHandler(button))

        # Start scheduler in a daemon thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

        logger.info("Starting bot...")
        application.run_polling(
            drop_pending_updates=True,  # Skip old updates
            close_loop=False
        )

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        if 'application' in locals() and application.running:
            application.stop()
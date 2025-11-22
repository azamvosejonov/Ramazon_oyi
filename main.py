import asyncio
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import admin_command, user_data, save_user_data, start, button, handle_message
from scheduler import schedule_daily_tasks, init_scheduler

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

# Global scheduler variable
scheduler = None

if __name__ == "__main__":
    from config import BOT_TOKEN

    try:
        # Initialize bot with post_init callback
        async def post_init_callback(application):
            # Initialize scheduler now that we have an event loop
            global scheduler
            scheduler = init_scheduler()
            scheduler.start()
            
            # Schedule initial tasks
            from handlers import user_data
            await schedule_daily_tasks(user_data)
        
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init_callback)
            .build()
        )

        # Add handlers with proper grouping
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CommandHandler('admin', admin_command))
        application.add_handler(CallbackQueryHandler(button))

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
        if 'scheduler' in locals() and scheduler.running:
            scheduler.shutdown()
import asyncio
import os
import logging
import signal
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers import admin_command, user_data, save_user_data, start, button, handle_message
from scheduler import schedule_daily_tasks, init_scheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')  # Log faylga ham yozish
    ]
)

# Disable verbose logging for httpx and apscheduler
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Our main logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global variables
scheduler = None
application = None


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram bot."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

    # User-ga xatolik haqida xabar berish (ixtiyoriy)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")


async def post_init_callback(app: Application) -> None:
    """Initialize scheduler after application starts."""
    global scheduler

    logger.info("Post-init callback started")

    try:
        # Initialize scheduler
        scheduler = init_scheduler()
        scheduler.start()
        logger.info("Scheduler started successfully")

        # Schedule daily tasks
        await schedule_daily_tasks(user_data)
        logger.info("Daily tasks scheduled successfully")

    except Exception as e:
        logger.error(f"Error in post_init_callback: {e}", exc_info=True)
        raise


async def shutdown(app: Application) -> None:
    """Cleanup on shutdown."""
    global scheduler

    logger.info("Shutting down bot...")

    try:
        # Save user data before shutdown
        save_user_data(user_data)
        logger.info("User data saved")

        # Stop scheduler
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    logger.info(f"Received signal {signum}")

    if application and application.running:
        asyncio.create_task(application.stop())

    sys.exit(0)


def main():
    """Main function to run the bot."""
    global application

    try:
        # Import token
        from config import BOT_TOKEN

        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in config.py")

        # Build application
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init_callback)
            .post_shutdown(shutdown)
            .build()
        )

        # Add error handler
        application.add_error_handler(error_handler)

        # Add command handlers
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('admin', admin_command))

        # Add message handlers (order matters!)
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("Bot started successfully!")
        logger.info("Press Ctrl+C to stop")

        # Start polling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    main()
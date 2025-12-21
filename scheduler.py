import asyncio
import logging
import os
import requests
import tempfile
from datetime import datetime, timedelta, time, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import pytz
from config import translations, BOT_TOKEN, CITIES
from utils import get_prayer_times, is_ramadan, generate_next_prayer_image, generate_dua_image
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.error import TelegramError, BadRequest, Forbidden

logger = logging.getLogger(__name__)

# Initialize bot
bot = Bot(token=BOT_TOKEN)

# Global scheduler
scheduler = None

# Cache for prayer times
prayer_times_cache = {}
CACHE_TTL = timedelta(minutes=30)

# User data cache
user_data_cache = {}


def init_scheduler():
    """Initialize the scheduler with the current event loop"""
    global scheduler

    if scheduler is None or not scheduler.running:
        scheduler = AsyncIOScheduler(
            timezone=pytz.timezone('Asia/Tashkent'),
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300
            }
        )
        logger.info("Scheduler initialized")

    return scheduler


async def send_message(chat_id, text, image_path=None, image_url=None):
    """Send message with optional image"""
    try:
        if image_url:
            # Download image from URL
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                with open(temp_file_path, 'rb') as photo:
                    await bot.send_photo(chat_id=chat_id, photo=photo, caption=text)
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        elif image_path:
            try:
                with open(image_path, 'rb') as photo:
                    await bot.send_photo(chat_id=chat_id, photo=photo, caption=text)
            finally:
                if os.path.exists(image_path):
                    os.remove(image_path)
        else:
            await bot.send_message(chat_id=chat_id, text=text)

    except Forbidden:
        logger.warning(f"Bot blocked by user {chat_id}")
    except TelegramError as e:
        logger.error(f"Telegram error sending message to {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending message to {chat_id}: {e}", exc_info=True)


async def send_prayer_times(chat_id):
    """Send prayer times to user"""
    try:
        from handlers import user_data

        user_info = user_data.get(str(chat_id), {})
        lang = user_info.get('lang', 'uz')
        city_key = user_info.get('city', 'tashkent')
        city_name = CITIES[city_key]['name']

        timings = await get_prayer_times(city_key)
        prayer_labels = translations[lang]['prayers']

        text = translations[lang]['prayer_times'].format(
            city=city_name,
            fajr=timings['Fajr'],
            dhuhr=timings['Dhuhr'],
            asr=timings['Asr'],
            maghrib=timings['Maghrib'],
            isha=timings['Isha']
        )

        # Replace labels
        for key, label in prayer_labels.items():
            text = text.replace(key, label.split()[0])

        await send_message(chat_id, text)

    except Exception as e:
        logger.error(f"Error sending prayer times to {chat_id}: {e}")


async def send_fasting_start(chat_id):
    """Send fasting start notification with dua"""
    try:
        from handlers import user_data

        user_info = user_data.get(str(chat_id), {})
        lang = user_info.get('lang', 'uz')

        image_url = "https://frankfurt.apollo.olxcdn.com/v1/files/09oo7o38yw1u2-UZ/image;s=1280x960"
        text = translations[lang]['fasting_start'].format(dua="")

        await send_message(chat_id, text, image_url=image_url)

    except Exception as e:
        logger.error(f"Error sending fasting start to {chat_id}: {e}")


async def send_fasting_end(chat_id):
    """Send fasting end notification with dua"""
    try:
        from handlers import user_data

        user_info = user_data.get(str(chat_id), {})
        lang = user_info.get('lang', 'uz')

        image_url = "https://frankfurt.apollo.olxcdn.com/v1/files/6i5j96fyzmpf1-UZ/image;s=960x1280"
        text = translations[lang]['fasting_end'].format(dua="")

        await send_message(chat_id, text, image_url=image_url)

    except Exception as e:
        logger.error(f"Error sending fasting end to {chat_id}: {e}")


async def send_prayer_notification(chat_id, prayer_name):
    """Send prayer time notification"""
    try:
        logger.info(f"Sending prayer notification to {chat_id} for {prayer_name}")
        from handlers import user_data

        user_info = user_data.get(str(chat_id), {})
        lang = user_info.get('lang', 'uz')

        prayer = translations[lang]['prayers'][prayer_name]
        text = translations[lang]['prayer_notification'].format(prayer=prayer)

        await send_message(chat_id, text)

    except Exception as e:
        logger.error(f"Error sending prayer notification to {chat_id}: {e}")


async def send_early_sahur(chat_id):
    """Send early sahur reminder"""
    try:
        from handlers import user_data

        user_info = user_data.get(str(chat_id), {})
        lang = user_info.get('lang', 'uz')
        text = translations[lang]['early_sahur']

        await send_message(chat_id, text)

    except Exception as e:
        logger.error(f"Error sending early sahur to {chat_id}: {e}")


async def send_early_iftar(chat_id):
    """Send early iftar reminder"""
    try:
        from handlers import user_data

        user_info = user_data.get(str(chat_id), {})
        lang = user_info.get('lang', 'uz')
        text = translations[lang]['early_iftar']

        await send_message(chat_id, text)

    except Exception as e:
        logger.error(f"Error sending early iftar to {chat_id}: {e}")


async def send_late_fasting_start(chat_id):
    """Send late fasting start reminder"""
    try:
        from handlers import user_data

        user_info = user_data.get(str(chat_id), {})
        lang = user_info.get('lang', 'uz')
        text = translations[lang]['late_fasting_start']

        await send_message(chat_id, text)

    except Exception as e:
        logger.error(f"Error sending late fasting start to {chat_id}: {e}")


async def update_menu_messages():
    """Update all active menu messages"""
    from handlers import user_data

    for chat_id_str in user_data:
        if not chat_id_str.isdigit():
            continue

        user_info = user_data[chat_id_str]

        if 'menu_msg' not in user_info:
            continue

        try:
            # Check last interaction
            last_interaction = user_info.get('last_interaction')
            if last_interaction:
                last_time = datetime.fromisoformat(last_interaction)
                if (datetime.now() - last_time).days > 1:
                    continue

            chat_id = int(chat_id_str)
            from handlers import send_menu
            await send_menu(chat_id, update_existing=True)

        except Exception as e:
            logger.debug(f"Menu update skipped for {chat_id_str}: {e}")


async def update_next_prayer_messages():
    """Update next prayer time messages"""
    from handlers import user_data
    from utils import get_next_prayer, calculate_remaining_time

    for chat_id_str, user_info in user_data.items():
        if not chat_id_str.isdigit() or 'next_prayer_msg' not in user_info:
            continue

        try:
            chat_id = int(chat_id_str)
            lang = user_info.get('lang', 'uz')
            city_key = user_info.get('city', 'tashkent')

            timings = await get_prayer_times(city_key)
            prayer, p_time = get_next_prayer(timings)

            # Calculate remaining time
            now = datetime.now()
            prayer_time = datetime.strptime(p_time, '%H:%M').replace(
                year=now.year,
                month=now.month,
                day=now.day
            )

            remaining = prayer_time - now

            # If prayer passed, remove message
            if remaining.total_seconds() < 0:
                del user_info['next_prayer_msg']
                continue

            # Generate and send updated image
            prayer_name = translations[lang]['prayers'][prayer]
            title = translations[lang]['next_prayer_title']

            image_path = generate_next_prayer_image(title, prayer_name, p_time, remaining, lang)

            with open(image_path, 'rb') as photo:
                media = InputMediaPhoto(photo)

                keyboard = [
                    [InlineKeyboardButton(
                        translations[lang]['update_button'],
                        callback_data='update_prayer_image'
                    )],
                    [InlineKeyboardButton(
                        translations[lang]['back_button'],
                        callback_data='back_to_menu'
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=user_info['next_prayer_msg'],
                    media=media,
                    reply_markup=reply_markup
                )

            # Clean up image
            if os.path.exists(image_path):
                os.remove(image_path)

        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.error(f"BadRequest updating next prayer for {chat_id}: {e}")
        except Exception as e:
            logger.error(f"Error updating next prayer for {chat_id}: {e}")


async def update_iftar_messages():
    """Update iftar countdown messages"""
    from handlers import user_data
    from utils import calculate_remaining_time

    for chat_id_str, user_info in user_data.items():
        if not chat_id_str.isdigit() or 'iftar_msg' not in user_info:
            continue

        try:
            chat_id = int(chat_id_str)
            lang = user_info.get('lang', 'uz')
            city_key = user_info.get('city', 'tashkent')

            timings = await get_prayer_times(city_key)
            now = datetime.now().time()
            fajr_time = datetime.strptime(timings['Fajr'], '%H:%M').time()

            if now < fajr_time:
                # Sahur time
                remaining = calculate_remaining_time(timings['Fajr'])
                text = f"Saharlikka qolgan vaqt: {remaining}\nSaharlik vaqti: {timings['Fajr']}"
            else:
                # Iftar time
                remaining = calculate_remaining_time(timings['Maghrib'])
                text = f"Iftorga qolgan vaqt: {remaining}\nIftor vaqti: {timings['Maghrib']}"

            image_path = generate_dua_image(text, lang)

            with open(image_path, 'rb') as photo:
                media = InputMediaPhoto(photo)

                keyboard = [
                    [InlineKeyboardButton(
                        translations[lang]['update_button'],
                        callback_data='update_iftar'
                    )],
                    [InlineKeyboardButton(
                        translations[lang]['back_button'],
                        callback_data='back_to_menu'
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=user_info['iftar_msg'],
                    media=media,
                    reply_markup=reply_markup
                )

            # Clean up
            if os.path.exists(image_path):
                os.remove(image_path)

        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.error(f"BadRequest updating iftar for {chat_id}: {e}")
        except Exception as e:
            logger.error(f"Error updating iftar for {chat_id}: {e}")


async def schedule_prayer_notifications():
    """Schedule prayer notifications for all users"""
    global user_data_cache

    logger.info("Scheduling prayer notifications for all users")

    for user_id, user_info in user_data_cache.items():
        if not user_id.isdigit():
            continue

        try:
            chat_id = int(user_id)
            city_key = user_info.get('city', 'tashkent')
            timings = await get_prayer_times(city_key)

            prayers = [
                ('Fajr', timings['Fajr']),
                ('Dhuhr', timings['Dhuhr']),
                ('Asr', timings['Asr']),
                ('Maghrib', timings['Maghrib']),
                ('Isha', timings['Isha'])
            ]

            for prayer, prayer_time in prayers:
                h, m = map(int, prayer_time.split(':'))

                scheduler.add_job(
                    send_prayer_notification,
                    CronTrigger(hour=h, minute=m),
                    args=[chat_id, prayer],
                    id=f'prayer_{prayer}_{chat_id}',
                    replace_existing=True
                )

                logger.debug(f"Scheduled {prayer} for user {chat_id} at {h}:{m}")

        except Exception as e:
            logger.error(f"Error scheduling prayers for user {user_id}: {e}")


async def schedule_fasting_notifications():
    """Schedule fasting-related notifications"""
    global user_data_cache

    logger.info(f"Scheduling fasting notifications for {len(user_data_cache)} users")

    for user_id, user_info in user_data_cache.items():
        if not user_id.isdigit():
            continue

        try:
            chat_id = int(user_id)
            city_key = user_info.get('city', 'tashkent')
            timings = await get_prayer_times(city_key)

            # Schedule sahur notifications
            if 'Imsak' in timings:
                imsak_h, imsak_m = map(int, timings['Imsak'].split(':'))
                imsak_dt = datetime.combine(date.today(), time(imsak_h, imsak_m))

                # Early sahur: 30 minutes before
                early_sahur_dt = imsak_dt - timedelta(minutes=30)
                scheduler.add_job(
                    send_early_sahur,
                    CronTrigger(hour=early_sahur_dt.hour, minute=early_sahur_dt.minute),
                    args=[chat_id],
                    id=f'early_sahur_{chat_id}',
                    replace_existing=True
                )

                # Fasting start at imsak
                scheduler.add_job(
                    send_fasting_start,
                    CronTrigger(hour=imsak_h, minute=imsak_m),
                    args=[chat_id],
                    id=f'fasting_start_{chat_id}',
                    replace_existing=True
                )

                # Late reminder: 30 minutes after
                late_dt = imsak_dt + timedelta(minutes=30)
                scheduler.add_job(
                    send_late_fasting_start,
                    CronTrigger(hour=late_dt.hour, minute=late_dt.minute),
                    args=[chat_id],
                    id=f'late_fasting_start_{chat_id}',
                    replace_existing=True
                )

            # Schedule iftar notifications
            if 'Maghrib' in timings:
                maghrib_h, maghrib_m = map(int, timings['Maghrib'].split(':'))
                maghrib_dt = datetime.combine(date.today(), time(maghrib_h, maghrib_m))

                # Early iftar: 2 minutes before
                early_iftar_dt = maghrib_dt - timedelta(minutes=2)
                scheduler.add_job(
                    send_early_iftar,
                    CronTrigger(hour=early_iftar_dt.hour, minute=early_iftar_dt.minute),
                    args=[chat_id],
                    id=f'early_iftar_{chat_id}',
                    replace_existing=True
                )

                # Fasting end at maghrib
                scheduler.add_job(
                    send_fasting_end,
                    CronTrigger(hour=maghrib_h, minute=maghrib_m),
                    args=[chat_id],
                    id=f'fasting_end_{chat_id}',
                    replace_existing=True
                )

        except Exception as e:
            logger.error(f"Error scheduling fasting for user {user_id}: {e}")


async def schedule_daily_tasks(user_data=None):
    """Schedule all daily tasks with optimized intervals"""
    global user_data_cache

    logger.info("Starting daily task scheduling")

    if user_data is not None:
        user_data_cache = user_data
        logger.info(f"User data cache updated: {len(user_data_cache)} entries")

    # Clear existing jobs
    jobs = scheduler.get_jobs()
    logger.info(f"Clearing {len(jobs)} existing jobs")
    for job in jobs:
        job.remove()

    # Schedule periodic updates
    scheduler.add_job(
        update_menu_messages,
        trigger=IntervalTrigger(minutes=15),
        id='update_menus',
        name='Update menu messages',
        replace_existing=True
    )

    scheduler.add_job(
        update_next_prayer_messages,
        trigger=IntervalTrigger(minutes=5),
        id='update_next_prayer',
        name='Update next prayer times',
        replace_existing=True
    )

    scheduler.add_job(
        update_iftar_messages,
        trigger=IntervalTrigger(minutes=15),
        id='update_iftar',
        name='Update iftar messages',
        replace_existing=True
    )

    # Schedule notifications
    await schedule_prayer_notifications()
    await schedule_fasting_notifications()

    logger.info(f"Daily tasks scheduled successfully. Total jobs: {len(scheduler.get_jobs())}")
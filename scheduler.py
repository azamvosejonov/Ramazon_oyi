import asyncio
import logging
import os
import requests
import tempfile
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import pytz
from config import translations, BOT_TOKEN, CITIES
from utils import get_prayer_times, is_ramadan, generate_next_prayer_image, generate_dua_image
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.error import TelegramError, BadRequest

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Reduce scheduler logging level

# Initialize bot
bot = Bot(token=BOT_TOKEN)

# Initialize scheduler with default settings
# We'll configure it with the event loop later
scheduler = None

def init_scheduler():
    """Initialize the scheduler with the current event loop"""
    global scheduler
    if scheduler is None or not scheduler.running:
        scheduler = AsyncIOScheduler(
            timezone=pytz.timezone('Asia/Tashkent'),
            event_loop=asyncio.get_event_loop(),
            job_defaults={
                'coalesce': True,  # Only run once if multiple triggers are missed
                'max_instances': 1,  # Only one instance of each job at a time
                'misfire_grace_time': 300  # 5 minutes grace period
            }
        )
    return scheduler

# Cache for prayer times to reduce API calls
prayer_times_cache = {}
CACHE_TTL = timedelta(minutes=30)

# Global variable to store user data
user_data_cache = {}

# Global chat_id
CHAT_ID = os.getenv('CHAT_ID')

async def send_message(chat_id, text, image_path=None, image_url=None):
    if image_url:
        # Download the image from URL
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Send the downloaded image
        with open(temp_file_path, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo, caption=text)
        
        # Clean up
        os.remove(temp_file_path)
    elif image_path:
        await bot.send_photo(chat_id=chat_id, photo=open(image_path, 'rb'), caption=text)
        os.remove(image_path)  # Clean up
    else:
        await bot.send_message(chat_id=chat_id, text=text)

async def send_prayer_times(chat_id):
    from handlers import user_data
    lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
    city_key = user_data.get(str(chat_id), {}).get('city', 'tashkent')
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
    # Replace the labels in text
    for key, label in prayer_labels.items():
        text = text.replace(key, label.split()[0])  # Remove emoji for times
    await send_message(chat_id, text)

async def send_fasting_start(chat_id):
    from handlers import user_data
    from utils import generate_dua_image
    lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
    city_key = user_data.get(str(chat_id), {}).get('city', 'tashkent')
    dua = translations[lang]['fasting_start_dua']
    image_url = "https://frankfurt.apollo.olxcdn.com/v1/files/09oo7o38yw1u2-UZ/image;s=1280x960"
    text = translations[lang]['fasting_start'].format(dua="")
    await send_message(chat_id, text, image_url=image_url)

async def send_fasting_end(chat_id):
    from handlers import user_data
    lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
    city_key = user_data.get(str(chat_id), {}).get('city', 'tashkent')
    
    # Image URL for the fasting end Dua (Iftor duosi)
    image_url = "https://frankfurt.apollo.olxcdn.com/v1/files/6i5j96fyzmpf1-UZ/image;s=960x1280"
    
    # Send the image directly
    text = translations[lang]['fasting_end'].format(dua="")
    await send_message(chat_id, text, image_url=image_url)

async def send_prayer_notification(chat_id, prayer_name):
    from handlers import user_data
    lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
    prayer = translations[lang]['prayers'][prayer_name]
    text = translations[lang]['prayer_notification'].format(prayer=prayer)
    await send_message(chat_id, text)

async def send_early_sahur(chat_id):
    from handlers import user_data
    lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
    text = translations[lang]['early_sahur']
    await send_message(chat_id, text)

async def send_early_iftar(chat_id):
    from handlers import user_data
    lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
    text = translations[lang]['early_iftar']
    await send_message(chat_id, text)

async def send_late_fasting_start(chat_id):
    from handlers import user_data
    lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
    text = translations[lang]['late_fasting_start']
    await send_message(chat_id, text)

async def update_menu_messages():
    """Update all active menu messages"""
    from handlers import user_data
    for chat_id_str in user_data:
        try:
            chat_id = int(chat_id_str)
            if 'menu_msg' in user_data[chat_id_str]:
                # Only update menu if user is active (last interaction within 1 day)
                last_interaction = user_data[chat_id_str].get('last_interaction')
                if last_interaction and (datetime.now() - datetime.fromisoformat(last_interaction)).days <= 1:
                    from handlers import send_menu
                    await send_menu(chat_id, update_existing=True)
        except Exception as e:
            logger.debug(f"Menu update skipped for {chat_id_str}: {e}")  # Debug level to reduce noise

async def update_next_prayer_messages():
    from handlers import user_data
    from datetime import datetime, timedelta
    
    for chat_id_str, data in user_data.items():
        if 'next_prayer_msg' in data:
            try:
                chat_id = int(chat_id_str)
                lang = data.get('lang', 'uz')
                city_key = data.get('city', 'tashkent')
                timings = await get_prayer_times(city_key)
                
                from utils import get_next_prayer, calculate_remaining_time
                prayer, p_time = get_next_prayer(timings)
                
                # Make sure remaining is a timedelta
                if isinstance(p_time, str):
                    # Parse the time string if needed
                    now = datetime.now()
                    prayer_time = datetime.strptime(p_time, '%H:%M').replace(
                        year=now.year, 
                        month=now.month, 
                        day=now.day
                    )
                    remaining = prayer_time - now
                else:
                    remaining = calculate_remaining_time(p_time)
                
                # Ensure remaining is a timedelta before calling total_seconds()
                if not isinstance(remaining, (timedelta, int, float)):
                    logger.error(f"Invalid remaining time type: {type(remaining)}")
                    continue
                    
                remaining_seconds = remaining.total_seconds() if hasattr(remaining, 'total_seconds') else float(remaining)
                
                if remaining_seconds < 0:
                    # Prayer time passed, remove the msg
                    del data['next_prayer_msg']
                    continue
                    
                prayer_name = translations[lang]['prayers'][prayer]
                title = translations[lang]['next_prayer_title']
                image_path = generate_next_prayer_image(title, prayer_name, p_time, remaining, lang)
                media = InputMediaPhoto(open(image_path, 'rb'))
                keyboard = [
                    [InlineKeyboardButton(translations[lang]['update_button'], callback_data='update_prayer_image')],
                    [InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                try:
                    await bot.edit_message_media(chat_id=chat_id, message_id=data['next_prayer_msg'], media=media, reply_markup=reply_markup)
                except BadRequest as e:
                    if "Message is not modified" in str(e):
                        pass  # Skip if same
                    else:
                        logger.error(f"Error updating message for chat {chat_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in update_next_prayer_messages for chat {chat_id}: {e}")

async def update_iftar_messages():
    from handlers import user_data
    for chat_id_str, data in user_data.items():
        if 'iftar_msg' not in data:
            continue
        chat_id = int(chat_id_str)
        lang = data.get('lang', 'uz')
        city_key = data.get('city', 'tashkent')
        try:
            timings = await get_prayer_times(city_key)
            now = datetime.now().time()
            fajr_time = datetime.strptime(timings['Fajr'], '%H:%M').time()
            maghrib_time = datetime.strptime(timings['Maghrib'], '%H:%M').time()
            if now < fajr_time:
                # Sahur time
                remaining = calculate_remaining_time(timings['Fajr'])
                text = f"Saharlikka qolgan vaqt: {remaining}\nSaharlik vaqti: {timings['Fajr']}"
            else:
                # Iftar time
                remaining = calculate_remaining_time(timings['Maghrib'])
                text = f"Iftorga qolgan vaqt: {remaining}\nIftor vaqti: {timings['Maghrib']}"
            image_path = generate_dua_image(text, lang)
            media = InputMediaPhoto(open(image_path, 'rb'))
            keyboard = [[InlineKeyboardButton(translations[lang]['update_button'], callback_data='update_iftar')], [InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await bot.edit_message_media(chat_id=chat_id, message_id=data['iftar_msg'], media=media, reply_markup=reply_markup)
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    pass  # Skip if same
                else:
                    raise
        except Exception as e:
            pass
        if 'menu_msg' in data:
            chat_id = int(chat_id_str)
            lang = data.get('lang', 'uz')
            city_key = data.get('city', 'tashkent')
            timings = await get_prayer_times(city_key)
            from utils import get_next_prayer, calculate_remaining_time
            prayer, p_time = get_next_prayer(timings)
            remaining = calculate_remaining_time(p_time)
            prayer_name = translations[lang]['prayers'][prayer]
            menu_text = translations[lang]['menu_msg']
            updated_text = f"{menu_text}\n\n🕰️ Keyingi namoz: {prayer_name} {p_time} ({remaining})"
            now = datetime.now().time()
            fajr_time = datetime.strptime(timings['Fajr'], '%H:%M').time()
            if now < fajr_time:
                iftar_button_text = "Saharlik vaqti"
            else:
                iftar_button_text = "Iftor vaqti"
            keyboard = []
            if is_ramadan():
                keyboard.append([InlineKeyboardButton(iftar_button_text, callback_data='iftar')])
            keyboard.extend([
                [InlineKeyboardButton(translations[lang]['next_prayer_button'], callback_data='next_prayer')],
                [InlineKeyboardButton(translations[lang]['ramadan_button'], callback_data='ramadan')],
            ])
            if is_ramadan():
                keyboard.extend([
                    [InlineKeyboardButton(translations[lang]['fasting_start_button'], callback_data='fasting_start')],
                    [InlineKeyboardButton(translations[lang]['fasting_end_button'], callback_data='fasting_end')],
                ])
            keyboard.append([InlineKeyboardButton(translations[lang]['change_city_button'], callback_data='change_city')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=data['menu_msg'], text=updated_text, reply_markup=reply_markup)
            except Exception as e:
                # Message not found, remove
                del data['menu_msg']

async def schedule_daily_tasks(user_data=None):
    """Schedule daily tasks for all users with optimized settings"""
    global user_data_cache
    
    if user_data is not None:
        user_data_cache = user_data
    
    # Clear existing jobs
    for job in scheduler.get_jobs():
        job.remove()
    
    # Schedule menu updates less frequently (every 15 minutes)
    scheduler.add_job(
        update_menu_messages,
        trigger=IntervalTrigger(minutes=15),
        id='update_menus',
        name='Update menu messages',
        replace_existing=True
    )
    
    # Schedule next prayer updates less frequently (every 5 minutes)
    scheduler.add_job(
        update_next_prayer_messages,
        trigger=IntervalTrigger(minutes=5),
        id='update_next_prayer',
        name='Update next prayer times',
        replace_existing=True
    )
    
    # Schedule iftar updates less frequently (every 15 minutes)
    scheduler.add_job(
        update_iftar_messages,
        trigger=IntervalTrigger(minutes=15),
        id='update_iftar',
        name='Update iftar messages',
        replace_existing=True
    )
    
    # Schedule prayer notifications
    await schedule_prayer_notifications()
    
    # Schedule fasting notifications for all users
    for user_id, user_info in user_data_cache.items():
        # Skip non-user entries (like notif_settings)
        if not user_id.isdigit():
            continue

        try:
            chat_id = int(user_id)
            city_key = user_info.get('city', 'tashkent')
            timings = await get_prayer_times(city_key)
            
            # Schedule fasting start at imsak
            if 'Imsak' in timings:
                imsak_h, imsak_m = map(int, timings['Imsak'].split(':'))
                scheduler.add_job(
                    lambda cid=chat_id: send_fasting_start(cid), 
                    CronTrigger(hour=imsak_h, minute=imsak_m), 
                    id=f'fasting_start_{chat_id}', 
                    replace_existing=True
                )
                
                # Late reminder: 30 minutes after imsak
                from datetime import datetime, time, timedelta, date
                imsak_dt = datetime.combine(date.today(), time(imsak_h, imsak_m))
                late_dt = imsak_dt + timedelta(minutes=30)
                scheduler.add_job(
                    lambda cid=chat_id: send_late_fasting_start(cid), 
                    CronTrigger(hour=late_dt.hour, minute=late_dt.minute), 
                    id=f'late_fasting_start_{chat_id}', 
                    replace_existing=True
                )
            
            # Schedule iftar and related times
            if 'Maghrib' in timings:
                maghrib_h, maghrib_m = map(int, timings['Maghrib'].split(':'))
                
                # Early iftar: 2 minutes before maghrib
                maghrib_dt = datetime.combine(date.today(), time(maghrib_h, maghrib_m))
                early_iftar_dt = maghrib_dt - timedelta(minutes=2)
                scheduler.add_job(
                    lambda cid=chat_id: send_early_iftar(cid), 
                    CronTrigger(hour=early_iftar_dt.hour, minute=early_iftar_dt.minute), 
                    id=f'early_iftar_{chat_id}', 
                    replace_existing=True
                )
                
                # Fasting end at maghrib
                scheduler.add_job(
                    lambda cid=chat_id: send_fasting_end(cid), 
                    CronTrigger(hour=maghrib_h, minute=maghrib_m), 
                    id=f'fasting_end_{chat_id}', 
                    replace_existing=True
                )
        except Exception as e:
            logger.error(f"Error scheduling fasting notifications for user {user_id}: {e}")

async def schedule_prayer_notifications():
    global user_data_cache
    # Schedule prayer notifications for all users
    for user_id, user_info in user_data_cache.items():
        # Skip non-user entries (like notif_settings)
        if not user_id.isdigit():
            continue

        try:
            chat_id = int(user_id)
            city_key = user_info.get('city', 'tashkent')
            timings = await get_prayer_times(city_key)

            # Prayer notifications
            prayers = [('Fajr', timings['Fajr']), ('Dhuhr', timings['Dhuhr']), ('Asr', timings['Asr']), ('Maghrib', timings['Maghrib']), ('Isha', timings['Isha'])]
            for prayer, t in prayers:
                h, m = map(int, t.split(':'))
                scheduler.add_job(
                    lambda p=prayer, cid=chat_id: send_prayer_notification(cid, p),
                    CronTrigger(hour=h, minute=m),
                    id=f'prayer_{prayer}_{chat_id}',
                    replace_existing=True
                )
        except Exception as e:
            logger.error(f"Error scheduling prayer notifications for user {user_id}: {e}")

import asyncio
import os
import sys
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append('.')

from scheduler import (
    send_prayer_times,
    send_fasting_start,
    send_fasting_end,
    send_prayer_notification,
    send_early_sahur,
    send_early_iftar,
    send_late_fasting_start
)

# Import config
from config import CITIES, BOT_TOKEN, translations

# Initialize bot
from telegram import Bot
bot = Bot(token=BOT_TOKEN)

# Initialize user data
from handlers import user_data, save_user_data

# Set test user data
test_user_id = str(os.getenv('ADMIN_ID'))
if test_user_id not in user_data:
    user_data[test_user_id] = {}
user_data[test_user_id].update({
    'lang': 'uz',
    'city': 'tashkent',
    'notif_settings': {
        'suhoor_before': 30,
        'iftar_before': 15,
        'prayer_notifs': True
    }
})
save_user_data(user_data)

# Test user data
TEST_CHAT_ID = os.getenv('ADMIN_ID')

async def test_all_notifications():
    print("🕌 Testing all prayer notifications...\n")
    
    # 1. Test prayer times
    print("1. Testing prayer times...")
    await send_prayer_times(TEST_CHAT_ID)
    
    # 2. Test fasting start (Saharlik)
    print("\n2. Testing fasting start (Saharlik)...")
    await send_fasting_start(TEST_CHAT_ID)
    
    # 3. Test fasting end (Iftorlik)
    print("\n3. Testing fasting end (Iftorlik)...")
    await send_fasting_end(TEST_CHAT_ID)
    
    # 4. Test prayer notifications for each prayer
    prayers = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
    for i, prayer in enumerate(prayers, 4):
        print(f"\n{i}. Testing {prayer} notification...")
        await send_prayer_notification(TEST_CHAT_ID, prayer)
    
    # 5. Test early sahur notification
    print("\n9. Testing early sahur notification...")
    await send_early_sahur(TEST_CHAT_ID)
    
    # 6. Test early iftar notification
    print("\n10. Testing early iftar notification...")
    await send_early_iftar(TEST_CHAT_ID)
    
    # 7. Test late fasting start notification
    print("\n11. Testing late fasting start notification...")
    await send_late_fasting_start(TEST_CHAT_ID)
    
    print("\n✅ All notification tests completed! Check your Telegram bot to verify the messages.")

if __name__ == '__main__':
    asyncio.run(test_all_notifications())

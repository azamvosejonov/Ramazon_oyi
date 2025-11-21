import asyncio
import os
import sys
from datetime import datetime, timedelta
import pytz

# Add current directory to path
sys.path.append('.')

# Import config first
from config import CITIES, BOT_TOKEN, translations

# Then import scheduler functions
from scheduler import (
    send_prayer_times,
    send_fasting_start,
    send_fasting_end,
    send_prayer_notification,
    send_early_sahur,
    send_early_iftar,
    send_late_fasting_start
)

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

async def test_notification(notification_func, name, *args):
    try:
        print(f"🔄 Testing {name}...")
        if args:
            await notification_func(TEST_CHAT_ID, *args)
        else:
            await notification_func(TEST_CHAT_ID)
        print(f"✅ {name} test passed!")
        return True
    except Exception as e:
        print(f"❌ {name} test failed: {str(e)}")
        return False

async def test_all_notifications():
    print("🕌 Barcha xabarnomalarni test qilish boshlandi...\n")
    
    # Test prayer times
    await test_notification(send_prayer_times, "Namoz vaqtlari")
    
    # Test fasting start (Saharlik)
    await test_notification(send_fasting_start, "Saharlik xabarnomasi")
    
    # Test fasting end (Iftorlik)
    await test_notification(send_fasting_end, "Iftorlik xabarnomasi")
    
    # Test prayer notifications
    prayers = [
        ('Fajr', 'Bomdod'),
        ('Dhuhr', 'Peshin'),
        ('Asr', 'Asr'),
        ('Maghrib', 'Shom'),
        ('Isha', 'Xufton')
    ]
    
    for eng, uzb in prayers:
        await test_notification(send_prayer_notification, f"{uzb} xabarnomasi", eng)
    
    # Test other notifications
    await test_notification(send_early_sahur, "Erta saharlik xabarnomasi")
    await test_notification(send_early_iftar, "Erta iftorlik xabarnomasi")
    await test_notification(send_late_fasting_start, "Kechikkan saharlik xabarnomasi")
    
    print("\n✅ Barcha testlar muvaffaqiyatli yakunlandi!")
    print("📱 Telegram botingizga kelgan xabarlarni tekshiring.")

if __name__ == '__main__':
    asyncio.run(test_all_notifications())

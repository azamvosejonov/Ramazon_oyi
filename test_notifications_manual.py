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

async def test_notification(notification_func, name):
    try:
        print(f"🔄 Testing {name}...")
        await notification_func(TEST_CHAT_ID)
        print(f"✅ {name} test passed!")
        return True
    except Exception as e:
        print(f"❌ {name} test failed: {str(e)}")
        return False

async def test_all_notifications():
    print("🕌 Starting notification tests...\n")
    
    tests = [
        (send_prayer_times, "Prayer Times"),
        (send_fasting_start, "Fasting Start (Saharlik)"),
        (send_fasting_end, "Fasting End (Iftorlik)"),
        (lambda chat_id: send_prayer_notification(chat_id, 'Fajr'), "Fajr Notification"),
        (send_early_sahur, "Early Sahur Reminder"),
        (send_early_iftar, "Early Iftar Reminder"),
        (send_late_fasting_start, "Late Fasting Start Reminder")
    ]
    
    results = []
    for func, name in tests:
        success = await test_notification(func, name)
        results.append((name, success))
        await asyncio.sleep(1)  # Small delay between tests
    
    # Print summary
    print("\n📊 Test Results:")
    print("-" * 50)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    # Print user data for verification
    print("\n🔍 Current Notification Settings:")
    print(f"- Saharlik: {user_data[test_user_id]['notif_settings'].get('suhoor_before', 'N/A')} min before")
    print(f"- Iftorlik: {user_data[test_user_id]['notif_settings'].get('iftar_before', 'N/A')} min before")
    print(f"- Prayer Notifications: {'✅ ON' if user_data[test_user_id]['notif_settings'].get('prayer_notifs', False) else '❌ OFF'}")

if __name__ == '__main__':
    asyncio.run(test_all_notifications())

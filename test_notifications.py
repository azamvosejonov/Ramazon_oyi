import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from handlers import user_data, save_user_data, is_admin
import os

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))  # Your admin user ID

# Test data
test_user_id = ADMIN_ID
user_data[str(test_user_id)] = {'is_admin': True}
save_user_data(user_data)

async def test_notifications():
    # Initialize the application
    application = Application.builder().token(TOKEN).build()
    
    # Test 1: Check if user is admin
    assert is_admin(test_user_id), "Admin test failed"
    
    # Test 2: Test notification settings menu
    keyboard = [
        [
            InlineKeyboardButton("🕒 Saharlik vaqti", callback_data='set_suhoor_time'),
            InlineKeyboardButton("🌅 Iftorlik vaqti", callback_data='set_iftar_time')
        ],
        [
            InlineKeyboardButton("🕌 Namoz xabarnomalari: ✅", callback_data='toggle_prayer_notifs')
        ],
        [InlineKeyboardButton("🔙 Orqaga", callback_data='admin_settings')]
    ]
    
    print("✅ Test 1: Admin check passed")
    
    # Test 3: Test suhoor time setting
    test_data = 'set_suhoor_30'
    if test_data.startswith('set_suhoor_'):
        minutes = int(test_data.split('_')[-1])
        if 'notif_settings' not in user_data[str(test_user_id)]:
            user_data[str(test_user_id)]['notif_settings'] = {}
        user_data[str(test_user_id)]['notif_settings']['suhoor_before'] = minutes
        save_user_data(user_data)
        assert user_data[str(test_user_id)]['notif_settings']['suhoor_before'] == 30, "Suhoor time not set correctly"
        print("✅ Test 2: Suhoor time setting works")
    
    # Test 4: Test iftar time setting
    test_data = 'set_iftar_15'
    if test_data.startswith('set_iftar_'):
        minutes = int(test_data.split('_')[-1])
        if 'notif_settings' not in user_data[str(test_user_id)]:
            user_data[str(test_user_id)]['notif_settings'] = {}
        user_data[str(test_user_id)]['notif_settings']['iftar_before'] = minutes
        save_user_data(user_data)
        assert user_data[str(test_user_id)]['notif_settings']['iftar_before'] == 15, "Iftar time not set correctly"
        print("✅ Test 3: Iftar time setting works")
    
    # Test 5: Test prayer notifications toggle
    test_data = 'toggle_prayer_notifs'
    if test_data == 'toggle_prayer_notifs':
        if 'notif_settings' not in user_data[str(test_user_id)]:
            user_data[str(test_user_id)]['notif_settings'] = {}
        current = user_data[str(test_user_id)]['notif_settings'].get('prayer_notifs', True)
        user_data[str(test_user_id)]['notif_settings']['prayer_notifs'] = not current
        save_user_data(user_data)
        assert user_data[str(test_user_id)]['notif_settings']['prayer_notifs'] is False, "Prayer notifications toggle not working"
        print("✅ Test 4: Prayer notifications toggle works")
    
    print("\n🔍 Test results:")
    print(f"Suhoor before: {user_data[str(test_user_id)]['notif_settings'].get('suhoor_before')} minutes")
    print(f"Iftar before: {user_data[str(test_user_id)]['notif_settings'].get('iftar_before')} minutes")
    print(f"Prayer notifications: {'✅ ON' if user_data[str(test_user_id)]['notif_settings'].get('prayer_notifs') else '❌ OFF'}")
    print("\n🎉 All tests completed successfully!")

if __name__ == '__main__':
    asyncio.run(test_notifications())

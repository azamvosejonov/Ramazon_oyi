import json
import os
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.error import BadRequest
from config import translations, CITIES
from utils import get_prayer_times, get_ramadan_progress, get_next_prayer, calculate_remaining_time, is_ramadan, generate_next_prayer_image, generate_dua_image

USER_DATA_FILE = 'user_data.json'

logger = logging.getLogger(__name__)

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def is_admin(chat_id):
    return str(chat_id) == os.getenv('ADMIN_ID')

def save_user_data(user_data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_data, f)

user_data = load_user_data()

# Store the last message ID for each chat
last_messages = {}

async def delete_previous_message(chat_id, context):
    """Delete the previous message sent by the bot in this chat."""
    if chat_id in last_messages:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_messages[chat_id])
        except Exception as e:
            # If message is already deleted or not found, just pass
            pass

# Only Uzbekistan is supported as a country

async def start(update, context):
    chat_id = update.effective_chat.id
    
    # Store the current message ID for future deletion
    if update.message:
        last_messages[chat_id] = update.message.message_id
    
    # Delete previous bot message if exists
    await delete_previous_message(chat_id, context)
    profile = user_data.setdefault(str(chat_id), {})
    lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
    
    # Create language selection keyboard with only supported languages
    keyboard = [
        [InlineKeyboardButton("O'zbek", callback_data='lang_uz')],
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Русский", callback_data='lang_ru')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text(translations[lang]['start_msg'], reply_markup=reply_markup)
    last_messages[chat_id] = message.message_id

async def button(update, context):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        return
    chat_id = query.message.chat_id
    data = query.data
    if data.startswith('lang_'):
        lang = data.split('_')[1]
        if str(chat_id) not in user_data:
            user_data[str(chat_id)] = {}
        user_data[str(chat_id)]['lang'] = lang
        # Automatically set country to Uzbekistan
        user_data[str(chat_id)]['country'] = 'uzbekistan'
        save_user_data(user_data)
        
        # Skip country selection and go directly to city selection
        keyboard = []
        for key, info in CITIES.items():
            if info['country'] == 'uzbekistan':
                keyboard.append([InlineKeyboardButton(info['name'], callback_data=f'city_{key}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=translations[lang]['select_city'], reply_markup=reply_markup)
    elif data.startswith('country_'):
        country_key = data.split('_')[1]
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        user_data[str(chat_id)]['country'] = country_key
        save_user_data(user_data)
        # Send city selection for the country
        keyboard = []
        for key, info in CITIES.items():
            if info['country'].lower().replace(' ', '_') == country_key:
                keyboard.append([InlineKeyboardButton(f"{info['name']}", callback_data=f'city_{key}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=translations[lang]['select_city'], reply_markup=reply_markup)
    elif data.startswith('city_'):
        city_key = data.split('_')[1]
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        user_data[str(chat_id)]['city'] = city_key
        save_user_data(user_data)
        try:
            city_name = CITIES[city_key]['name']
        except KeyError:
            city_name = city_key  # Fallback
        try:
            text = translations[lang]['city_selected'].format(city=city_name)
        except KeyError:
            text = f"Shahar tanlandi: {city_name}"  # Fallback
        # Send menu
        keyboard = [
            [InlineKeyboardButton(translations[lang]['iftar_button'], callback_data='iftar')],
            [InlineKeyboardButton(translations[lang]['next_prayer_button'], callback_data='next_prayer')],
            [InlineKeyboardButton(translations[lang]['ramadan_button'], callback_data='ramadan')],
            [InlineKeyboardButton(translations[lang]['fasting_start_button'], callback_data='fasting_start')],
            [InlineKeyboardButton(translations[lang]['fasting_end_button'], callback_data='fasting_end')],
            [InlineKeyboardButton(translations[lang]['change_city_button'], callback_data='change_city')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = await query.edit_message_text(text=text + "\n\n" + translations[lang]['menu_msg'], reply_markup=reply_markup)
        user_data[str(chat_id)]['menu_msg'] = message.message_id
    elif data == 'change_city':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        # Show Uzbek cities directly
        keyboard = []
        for key, info in CITIES.items():
            keyboard.append([InlineKeyboardButton(info['name'], callback_data=f'city_{key}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=translations[lang]['select_city'], reply_markup=reply_markup)
    elif data == 'iftar':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        if not is_ramadan():
            text = translations[lang]['not_ramadan']
            keyboard = [[InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            from datetime import datetime
            city_key = user_data.get(str(chat_id), {}).get('city', 'tashkent')
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
            message = await query.edit_message_media(media=media, reply_markup=reply_markup)
            user_data[str(chat_id)]['iftar_msg'] = message.message_id

    elif data == 'ramadan':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        if not is_ramadan():
            text = translations[lang]['not_ramadan']
            keyboard = [[InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            progress = get_ramadan_progress()
            if progress:
                day, left, end_date = progress
                text = translations[lang]['ramadan_progress'].format(day=day, left=left, end_date=end_date)
            else:
                text = translations[lang]['not_ramadan']  # Fallback
            keyboard = [[InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=text, reply_markup=reply_markup)

    elif data == 'fasting_start':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        if not is_ramadan():
            text = translations[lang]['not_ramadan']
            keyboard = [[InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            dua = translations[lang]['fasting_start_dua']
            image_path = generate_dua_image(dua, lang)
            media = InputMediaPhoto(open(image_path, 'rb'))
            keyboard = [[InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_media(media=media, reply_markup=reply_markup)

    elif data == 'fasting_end':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        if not is_ramadan():
            text = translations[lang]['not_ramadan']
            keyboard = [[InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            dua = translations[lang]['fasting_end_dua']
            image_path = generate_dua_image(dua, lang)
            media = InputMediaPhoto(open(image_path, 'rb'))
            keyboard = [[InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_media(media=media, reply_markup=reply_markup)

    elif data == 'back_to_menu':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        text = translations[lang]['menu_msg']
        keyboard = [
            [InlineKeyboardButton(translations[lang]['iftar_button'], callback_data='iftar')],
            [InlineKeyboardButton(translations[lang]['next_prayer_button'], callback_data='next_prayer')],
            [InlineKeyboardButton(translations[lang]['ramadan_button'], callback_data='ramadan')],
            [InlineKeyboardButton(translations[lang]['fasting_start_button'], callback_data='fasting_start')],
            [InlineKeyboardButton(translations[lang]['fasting_end_button'], callback_data='fasting_end')],
            [InlineKeyboardButton(translations[lang]['change_city_button'], callback_data='change_city')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            message = await query.edit_message_text(text=text, reply_markup=reply_markup)
            user_data[str(chat_id)]['menu_msg'] = message.message_id
        except BadRequest:
            # If message is media, send new message
            message = await query.message.reply_text(text=text, reply_markup=reply_markup)
            user_data[str(chat_id)]['menu_msg'] = message.message_id
    elif data == 'next_prayer':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        city_key = user_data.get(str(chat_id), {}).get('city', 'tashkent')
        timings = await get_prayer_times(city_key)
        prayer, p_time = get_next_prayer(timings)
        remaining = calculate_remaining_time(p_time)
        prayer_name = translations[lang]['prayers'][prayer]
        title = translations[lang]['next_prayer_title']
        image_path = generate_next_prayer_image(title, prayer_name, p_time, remaining, lang)
        media = InputMediaPhoto(open(image_path, 'rb'))
        keyboard = [[InlineKeyboardButton(translations[lang]['update_button'], callback_data='update_prayer_image')], [InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = await query.edit_message_media(media=media, reply_markup=reply_markup)
        user_data[str(chat_id)]['next_prayer_msg'] = message.message_id

    elif data == 'update_prayer_image':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        city_key = user_data.get(str(chat_id), {}).get('city', 'tashkent')
        timings = await get_prayer_times(city_key)
        prayer, p_time = get_next_prayer(timings)
        remaining = calculate_remaining_time(p_time)
        prayer_name = translations[lang]['prayers'][prayer]
        title = translations[lang]['next_prayer_title']
        image_path = generate_next_prayer_image(title, prayer_name, p_time, remaining, lang)
        media = InputMediaPhoto(open(image_path, 'rb'))
        keyboard = [[InlineKeyboardButton(translations[lang]['update_button'], callback_data='update_prayer_image')], [InlineKeyboardButton(translations[lang]['back_button'], callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_media(media=media, reply_markup=reply_markup)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                await query.answer("Ma'lumot o'zgarmagan")
            else:
                raise

    elif data == 'update_iftar':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        city_key = user_data.get(str(chat_id), {}).get('city', 'tashkent')
        timings = await get_prayer_times(city_key)
        from datetime import datetime
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
            await query.edit_message_media(media=media, reply_markup=reply_markup)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                await query.answer("Ma'lumot o'zgarmagan")  # Info not changed
            else:
                raise

    elif data == 'back_to_menu':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        text = translations[lang]['menu_msg']
        keyboard = [
            [InlineKeyboardButton(translations[lang]['iftar_button'], callback_data='iftar')],
            [InlineKeyboardButton(translations[lang]['next_prayer_button'], callback_data='next_prayer')],
            [InlineKeyboardButton(translations[lang]['ramadan_button'], callback_data='ramadan')],
            [InlineKeyboardButton(translations[lang]['fasting_start_button'], callback_data='fasting_start')],
            [InlineKeyboardButton(translations[lang]['fasting_end_button'], callback_data='fasting_end')],
            [InlineKeyboardButton(translations[lang]['change_city_button'], callback_data='change_city')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            message = await query.edit_message_text(text=text, reply_markup=reply_markup)
            user_data[str(chat_id)]['menu_msg'] = message.message_id
        except BadRequest:
            # If message is media, send new message
            message = await query.message.reply_text(text=text, reply_markup=reply_markup)
            user_data[str(chat_id)]['menu_msg'] = message.message_id

    elif data == 'back_to_menu':
        lang = user_data.get(str(chat_id), {}).get('lang', 'uz')
        text = translations[lang]['menu_msg']
        keyboard = [
            [InlineKeyboardButton(translations[lang]['iftar_button'], callback_data='iftar')],
            [InlineKeyboardButton(translations[lang]['next_prayer_button'], callback_data='next_prayer')],
            [InlineKeyboardButton(translations[lang]['ramadan_button'], callback_data='ramadan')],
            [InlineKeyboardButton(translations[lang]['fasting_start_button'], callback_data='fasting_start')],
            [InlineKeyboardButton(translations[lang]['fasting_end_button'], callback_data='fasting_end')],
            [InlineKeyboardButton(translations[lang]['change_city_button'], callback_data='change_city')],]
        if is_admin(chat_id):
            keyboard.append([InlineKeyboardButton('Admin Panel', callback_data='admin_panel')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            message = await query.edit_message_text(text=text, reply_markup=reply_markup)
            user_data[str(chat_id)]['menu_msg'] = message.message_id
        except BadRequest:
            # If message is media, send new message
            message = await query.message.reply_text(text=text, reply_markup=reply_markup)
            user_data[str(chat_id)]['menu_msg'] = message.message_id

    elif data == 'user_stats':
        if not is_admin(chat_id):
            await query.answer("Siz admin emassiz!")
            return
        total_users = len(user_data)
        from datetime import datetime
        active_today = sum(1 for u in user_data.values() if u.get('last_seen', '').startswith(datetime.now().date().isoformat()))
        new_today = sum(1 for u in user_data.values() if u.get('last_seen', '').startswith(datetime.now().date().isoformat()) and not u.get('lang'))
        text = f"Umumiy foydalanuvchilar: {total_users}\nBugun faollar: {active_today}\nBugun yangilar: {new_today}"
        keyboard = [[InlineKeyboardButton("Orqaga", callback_data='admin_panel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    elif data == 'send_ad':
        if not is_admin(chat_id):
            await query.answer("Siz admin emassiz!")
            return
        # Store that we're expecting an ad from this admin
        user_data[str(chat_id)]['awaiting_ad'] = True
        save_user_data(user_data)
        
        text = """📢 Reklama yuborish uchun quyidagilardan birini yuboring:
        
• Matn
• Rasm
• Video
• Link
• Yoki ularning kombinatsiyasi

Barcha foydalanuvchilarga yuboriladi."""
        keyboard = [
            [InlineKeyboardButton("Bekor qilish", callback_data='admin_panel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        except BadRequest:
            await query.message.reply_text(text=text, reply_markup=reply_markup)

    elif data == 'delete_ad':
        if not is_admin(chat_id):
            await query.answer("Siz admin emassiz!")
            return
        # Assume ad_message_id is stored in user_data
        for uid, data in user_data.items():
            if 'ad_msg' in data:
                try:
                    await context.bot.delete_message(chat_id=uid, message_id=data['ad_msg'])
                    del data['ad_msg']
                except:
                    pass
        save_user_data(user_data)
        await query.edit_message_text(text="Reklama o'chirildi", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Orqaga", callback_data='admin_panel')]]))
    
    elif data == 'admin_panel':
        if not is_admin(chat_id):
            await query.answer("Siz admin emassiz!")
            return
            
        # Import datetime here to ensure it's available in the local scope
        from datetime import datetime
        
        total_users = len(user_data)
        today = datetime.now().date().isoformat()
        active_today = 0
        
        # Safely count active users today
        for u in user_data.values():
            last_seen = u.get('last_seen', '')
            if last_seen and isinstance(last_seen, str):
                if last_seen.startswith(today):
                    active_today += 1
        
        text = f"""<b>👨‍💻 Admin Panel</b>
        
📊 Bot boshqaruv paneliga xush kelibsiz!

📈 <b>Statistika:</b>
• 👥 Jami foydalanuvchilar: {total_users} ta
• 🟢 Bugungi faollar: {active_today} ta

Quyidagi bo'limlardan birini tanlang:"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Foydalanuvchilar statistikasi", callback_data='user_stats')],
            [InlineKeyboardButton("🌍 Foydalanuvchilar manzillari", callback_data='user_locations')],
            [InlineKeyboardButton("📢 Reklama yuborish", callback_data='send_ad')],
            [InlineKeyboardButton("🗑️ Reklamani o'chirish", callback_data='delete_ad')],
            [InlineKeyboardButton("⚙️ Sozlamalar", callback_data='admin_settings')],
            [InlineKeyboardButton("🔙 Asosiy menyu", callback_data='back_to_menu')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                text=text, 
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except BadRequest:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    
    elif data == 'user_locations':
        if not is_admin(chat_id):
            await query.answer("Siz admin emassiz!")
            return
            
        # Group users by city
        locations = {}
        for uid, data in user_data.items():
            city = data.get('city', 'Noma\'lum')
            if city not in locations:
                locations[city] = 0
            locations[city] += 1
        
        # Format the message
        text = "<b>🌍 Foydalanuvchilar manzillari</b>\n\n"
        for city, count in sorted(locations.items(), key=lambda x: x[1], reverse=True):
            text += f"• {city}: {count} ta foydalanuvchi\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Yangilash", callback_data='user_locations')],
            [InlineKeyboardButton("🔙 Orqaga", callback_data='admin_panel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except BadRequest:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    
    elif data == 'admin_settings':
        if not is_admin(chat_id):
            await query.answer("Siz admin emassiz!")
            return
            
        text = """<b>⚙️ Admin Sozlamalari</b>

Quyidagi sozlamalarni o'zgartirishingiz mumkin:"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Bot statistikasini o'chirish", callback_data='clear_stats')],
            [InlineKeyboardButton("🔔 Xabarnomalarni sozlash", callback_data='notif_settings')],
            [InlineKeyboardButton("🔙 Orqaga", callback_data='admin_panel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except BadRequest:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
    elif data == 'notif_settings':
        if not is_admin(chat_id):
            await query.answer("Siz admin emassiz!")
            return
            
        # Get current settings or defaults
        suhoor_before = user_data.get('notif_settings', {}).get('suhoor_before', 30)  # Default 30 minutes
        iftar_before = user_data.get('notif_settings', {}).get('iftar_before', 10)    # Default 10 minutes
        prayer_notifs = user_data.get('notif_settings', {}).get('prayer_notifs', True)  # Default on
        
        status = '✅ Yoqilgan' if prayer_notifs else '❌ O\'chirilgan'
        text = f"""<b>🔔 Xabarnoma Sozlamalari</b>

🕒 <b>Saharlik xabarnomasi:</b> {suhoor_before} daqiqa oldin
🌅 <b>Iftorlik xabarnomasi:</b> {iftar_before} daqiqa oldin
🕌 <b>Namoz vaqtlari xabarnomalari:</b> {status}

Quyidagi sozlamalarni o'zgartirishingiz mumkin:"""
        
        keyboard = [
            [
                InlineKeyboardButton("🕒 Saharlik vaqti", callback_data='set_suhoor_time'),
                InlineKeyboardButton("🌅 Iftorlik vaqti", callback_data='set_iftar_time')
            ],
            [
                InlineKeyboardButton("🕌 Namoz xabarnomalari: " + ("✅" if prayer_notifs else "❌"), 
                                  callback_data='toggle_prayer_notifs')
            ],
            [InlineKeyboardButton("🔙 Orqaga", callback_data='admin_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except BadRequest:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
    elif data == 'set_suhoor_time':
        keyboard = [
            [InlineKeyboardButton(f"{i} daqiqa", callback_data=f'set_suhoor_{i}')] 
            for i in [15, 30, 45, 60]
        ]
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data='notif_settings')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🕒 Saharlikdan necha daqiqa oldin xabar yuborilsin?",
            reply_markup=reply_markup
        )
        
    elif data == 'set_iftar_time':
        keyboard = [
            [InlineKeyboardButton(f"{i} daqiqa", callback_data=f'set_iftar_{i}')] 
            for i in [5, 10, 15, 30]
        ]
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data='notif_settings')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🌅 Iftorlikdan necha daqiqa oldin xabar yuborilsin?",
            reply_markup=reply_markup
        )
        
    elif data.startswith('set_suhoor_'):
        minutes = int(data.split('_')[-1])
        if 'notif_settings' not in user_data:
            user_data['notif_settings'] = {}
        user_data['notif_settings']['suhoor_before'] = minutes
        save_user_data(user_data)
        await query.answer(f"✅ Saharlikdan {minutes} daqiqa oldin xabar yuboriladi")
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data='notif_settings')]
            ])
        )
        
    elif data.startswith('set_iftar_'):
        minutes = int(data.split('_')[-1])
        if 'notif_settings' not in user_data:
            user_data['notif_settings'] = {}
        user_data['notif_settings']['iftar_before'] = minutes
        save_user_data(user_data)
        await query.answer(f"✅ Iftorlikdan {minutes} daqiqa oldin xabar yuboriladi")
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Orqaga", callback_data='notif_settings')]
            ])
        )
        
    elif data == 'toggle_prayer_notifs':
        if 'notif_settings' not in user_data:
            user_data['notif_settings'] = {}
        current = user_data['notif_settings'].get('prayer_notifs', True)
        user_data['notif_settings']['prayer_notifs'] = not current
        save_user_data(user_data)
        status = 'yoqildi' if not current else 'o\'chirildi'
        await query.answer(f"✅ Namoz vaqti xabarnomalari {status}")
        # Update the button text
        keyboard = [list(row) for row in query.message.reply_markup.inline_keyboard]
        keyboard[1][0] = InlineKeyboardButton(
            f"🕌 Namoz vaqtlari: {'✅' if not current else '❌'}", 
            callback_data='toggle_prayer_notifs'
        )
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
async def handle_message(update, context):
    chat_id = update.effective_chat.id
    user_id = str(chat_id)
    
    # Check if this is an admin sending an ad
    if user_id in user_data and user_data[user_id].get('awaiting_ad') and is_admin(chat_id):
        sent_count = 0
        error_count = 0
        total_users = len([uid for uid in user_data.keys() if uid != user_id])
        
        # Send a processing message
        status_msg = await update.message.reply_text(f"⏳ Reklama foydalanuvchilarga yuborilmoqda...\nJami: {total_users} ta")
        
        # Prepare media and caption
        caption = update.message.caption or update.message.text or ""
        
        # Add signature if not present
        if not any(word in caption.lower() for word in ['@', 'kanal', 'kanalimiz', 'guruh', 'guruhimiz']):
            caption += "\n\n@Ramazon_va_Namoz_bot"
        
        # Send to all users
        for user_chat_id in user_data:
            if user_chat_id == user_id:  # Skip sending to self
                continue
                
            try:
                # Handle different message types
                if update.message.photo:
                    photo = update.message.photo[-1]  # Get highest resolution
                    await context.bot.send_photo(
                        chat_id=user_chat_id,
                        photo=photo.file_id,
                        caption=caption,
                        parse_mode='HTML'
                    )
                elif update.message.video:
                    video = update.message.video
                    await context.bot.send_video(
                        chat_id=user_chat_id,
                        video=video.file_id,
                        caption=caption,
                        parse_mode='HTML'
                    )
                elif update.message.text:
                    await context.bot.send_message(
                        chat_id=user_chat_id,
                        text=caption,
                        parse_mode='HTML',
                        disable_web_page_preview=not any(word in caption.lower() for word in ['http', 'www', '.com', '.uz'])
                    )
                sent_count += 1
                
                # Update progress every 10 messages
                if sent_count % 10 == 0:
                    await status_msg.edit_text(
                        f"⏳ Reklama yuborilmoqda...\n"
                        f"✅ Yuborildi: {sent_count}/{total_users}\n"
                        f"❌ Xatolik: {error_count}"
                    )
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error sending ad to {user_chat_id}: {e}")
                
        # Clean up
        user_data[user_id].pop('awaiting_ad', None)
        save_user_data(user_data)
        
        # Send completion message
        await status_msg.edit_text(
            f"✅ Reklama muvaffaqiyatli yuborildi!\n"
            f"🔢 Jami: {total_users} ta\n"
            f"✅ Muvaffaqiyatli: {sent_count}\n"
            f"❌ Xatolik: {error_count}"
        )
        
        # Return to admin panel
        await admin_command(update, context)
        return
        
    # Handle non-admin or regular messages
    # ... (rest of your existing handle_message function)

async def admin_command(update, context):
    chat_id = update.effective_chat.id
    if not is_admin(chat_id):
        await update.message.reply_text("Siz admin emassiz!")
        return
    
    # Reset awaiting_ad state when entering admin panel
    if str(chat_id) in user_data:
        user_data[str(chat_id)].pop('awaiting_ad', None)
    
    text = """<b>Admin Panel</b>\n\nQuyidagi bo'limlardan birini tanlang:"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Foydalanuvchilar Statistika", callback_data='user_stats')],
        [InlineKeyboardButton("📢 Reklama Yuborish", callback_data='send_ad')],
        [InlineKeyboardButton("🗑 Reklamani O'chirish", callback_data='delete_ad')],
        [InlineKeyboardButton("🔙 Orqaga", callback_data='back_to_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')
        except BadRequest:
            await update.callback_query.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

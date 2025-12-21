import json
import os
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Bot
from telegram.error import BadRequest, Forbidden, TelegramError
from config import translations, CITIES, BOT_TOKEN
from utils import (
    get_prayer_times, get_ramadan_progress, get_next_prayer,
    calculate_remaining_time, is_ramadan, generate_next_prayer_image,
    generate_dua_image, get_local_datetime, get_local_time
)

logger = logging.getLogger(__name__)

USER_DATA_FILE = 'user_data.json'

# Store last messages
last_messages = {}


def load_user_data():
    """Load user data from JSON file"""
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading user data: {e}", exc_info=True)
        return {}


def save_user_data(data):
    """Save user data to JSON file"""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving user data: {e}", exc_info=True)


def is_admin(chat_id):
    """Check if user is admin"""
    admin_id = os.getenv('ADMIN_ID')
    return admin_id and str(chat_id) == admin_id


# Load user data
user_data = load_user_data()


async def delete_previous_message(chat_id, context):
    """Delete previous bot message"""
    if chat_id in last_messages:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=last_messages[chat_id]
            )
        except Exception:
            pass


async def update_user_activity(chat_id):
    """Update user's last activity time"""
    user_id = str(chat_id)
    if user_id not in user_data:
        user_data[user_id] = {}

    user_data[user_id]['last_seen'] = datetime.now().isoformat()
    user_data[user_id]['last_interaction'] = datetime.now().isoformat()
    save_user_data(user_data)


async def start(update, context):
    """Handle /start command"""
    chat_id = update.effective_chat.id

    try:
        # Store message ID
        if update.message:
            last_messages[chat_id] = update.message.message_id

        # Delete previous message
        await delete_previous_message(chat_id, context)

        # Initialize user profile
        user_id = str(chat_id)
        if user_id not in user_data:
            user_data[user_id] = {}

        await update_user_activity(chat_id)

        lang = user_data.get(user_id, {}).get('lang', 'uz')

        # Language selection keyboard
        keyboard = [
            [InlineKeyboardButton("O'zbek 🇺🇿", callback_data='lang_uz')],
            [InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')],
            [InlineKeyboardButton("Русский 🇷🇺", callback_data='lang_ru')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message = await update.message.reply_text(
            translations[lang]['start_msg'],
            reply_markup=reply_markup
        )
        last_messages[chat_id] = message.message_id

    except Exception as e:
        logger.error(f"Error in start command for {chat_id}: {e}", exc_info=True)

        # Fallback
        try:
            await update.message.reply_text(
                "Salom! Tilni tanlang / Hello! Choose language:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("O'zbek", callback_data='lang_uz')],
                    [InlineKeyboardButton("English", callback_data='lang_en')],
                    [InlineKeyboardButton("Русский", callback_data='lang_ru')]
                ])
            )
        except Exception as e2:
            logger.error(f"Fallback failed for {chat_id}: {e2}")


async def button(update, context):
    """Handle button callbacks"""
    query = update.callback_query

    try:
        await query.answer()
    except BadRequest:
        return

    chat_id = query.message.chat_id
    data = query.data

    await update_user_activity(chat_id)

    try:
        # Language selection
        if data.startswith('lang_'):
            await handle_language_selection(query, data)

        # City selection
        elif data.startswith('city_'):
            await handle_city_selection(query, data)

        # Menu actions
        elif data == 'change_city':
            await handle_change_city(query)
        elif data == 'iftar':
            await handle_iftar(query)
        elif data == 'ramadan':
            await handle_ramadan(query)
        elif data == 'fasting_start':
            await handle_fasting_start(query)
        elif data == 'fasting_end':
            await handle_fasting_end(query)
        elif data == 'next_prayer':
            await handle_next_prayer(query)
        elif data == 'back_to_menu':
            await handle_back_to_menu(query, chat_id)

        # Update actions
        elif data == 'update_prayer_image':
            await handle_update_prayer(query)
        elif data == 'update_iftar':
            await handle_update_iftar(query)

        # Admin actions
        elif data == 'admin_panel':
            await handle_admin_panel(query, chat_id)
        elif data == 'user_stats':
            await handle_user_stats(query, chat_id)
        elif data == 'user_locations':
            await handle_user_locations(query, chat_id)
        elif data == 'send_ad':
            await handle_send_ad(query, chat_id)
        elif data == 'delete_ad':
            await handle_delete_ad(query, chat_id, context)
        elif data == 'admin_settings':
            await handle_admin_settings(query, chat_id)
        elif data == 'notif_settings':
            await handle_notif_settings(query, chat_id)
        elif data.startswith('set_suhoor_'):
            await handle_set_suhoor(query, data)
        elif data.startswith('set_iftar_'):
            await handle_set_iftar(query, data)
        elif data == 'set_suhoor_time':
            await handle_set_suhoor_time(query)
        elif data == 'set_iftar_time':
            await handle_set_iftar_time(query)
        elif data == 'toggle_prayer_notifs':
            await handle_toggle_prayer_notifs(query)

    except Exception as e:
        logger.error(f"Error handling callback {data} for {chat_id}: {e}", exc_info=True)
        try:
            await query.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        except Exception:
            pass


async def handle_language_selection(query, data):
    """Handle language selection"""
    lang = data.split('_')[1]
    chat_id = query.message.chat_id
    user_id = str(chat_id)

    if user_id not in user_data:
        user_data[user_id] = {}

    user_data[user_id]['lang'] = lang
    user_data[user_id]['country'] = 'uzbekistan'
    save_user_data(user_data)

    # Show city selection
    keyboard = []
    for key, info in CITIES.items():
        if info['country'] == 'uzbekistan':
            keyboard.append([
                InlineKeyboardButton(info['name'], callback_data=f'city_{key}')
            ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=translations[lang]['select_city'],
        reply_markup=reply_markup
    )


async def handle_city_selection(query, data):
    """Handle city selection"""
    city_key = data.split('_')[1]
    chat_id = query.message.chat_id
    user_id = str(chat_id)

    lang = user_data.get(user_id, {}).get('lang', 'uz')
    user_data[user_id]['city'] = city_key
    save_user_data(user_data)

    city_name = CITIES.get(city_key, {}).get('name', city_key)
    text = translations[lang]['city_selected'].format(city=city_name)

    # Show menu
    keyboard = [
        [InlineKeyboardButton(
            translations[lang]['next_prayer_button'],
            callback_data='next_prayer'
        )],
        [InlineKeyboardButton(
            translations[lang]['ramadan_button'],
            callback_data='ramadan'
        )],
    ]

    if is_ramadan():
        keyboard.insert(0, [InlineKeyboardButton(
            translations[lang]['iftar_button'],
            callback_data='iftar'
        )])
        keyboard.extend([
            [InlineKeyboardButton(
                translations[lang]['fasting_start_button'],
                callback_data='fasting_start'
            )],
            [InlineKeyboardButton(
                translations[lang]['fasting_end_button'],
                callback_data='fasting_end'
            )],
        ])

    keyboard.append([InlineKeyboardButton(
        translations[lang]['change_city_button'],
        callback_data='change_city'
    )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await query.edit_message_text(
        text=text + "\n\n" + translations[lang]['menu_msg'],
        reply_markup=reply_markup
    )
    user_data[user_id]['menu_msg'] = message.message_id


async def handle_change_city(query):
    """Handle change city request"""
    chat_id = query.message.chat_id
    user_id = str(chat_id)
    lang = user_data.get(user_id, {}).get('lang', 'uz')

    keyboard = []
    for key, info in CITIES.items():
        keyboard.append([
            InlineKeyboardButton(info['name'], callback_data=f'city_{key}')
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=translations[lang]['select_city'],
        reply_markup=reply_markup
    )


async def handle_iftar(query):
    """Handle iftar time request"""
    chat_id = query.message.chat_id
    user_id = str(chat_id)
    lang = user_data.get(user_id, {}).get('lang', 'uz')

    if not is_ramadan():
        keyboard = [[InlineKeyboardButton(
            translations[lang]['back_button'],
            callback_data='back_to_menu'
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=translations[lang]['not_ramadan'],
            reply_markup=reply_markup
        )
        return

    city_key = user_data.get(user_id, {}).get('city', 'tashkent')
    timings = await get_prayer_times(city_key)
    now = get_local_time()
    fajr_time = datetime.strptime(timings['Fajr'], '%H:%M').time()

    if now < fajr_time:
        remaining = calculate_remaining_time(timings['Fajr'])
        text = f"Saharlikka qolgan vaqt: {remaining}\nSaharlik vaqti: {timings['Fajr']}"
    else:
        remaining = calculate_remaining_time(timings['Maghrib'])
        text = f"Iftorga qolgan vaqt: {remaining}\nIftor vaqti: {timings['Maghrib']}"

    image_path = generate_dua_image(text, lang)

    try:
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
            message = await query.edit_message_media(
                media=media,
                reply_markup=reply_markup
            )
            user_data[user_id]['iftar_msg'] = message.message_id
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


async def handle_ramadan(query):
    """Handle Ramadan info request"""
    chat_id = query.message.chat_id
    user_id = str(chat_id)
    lang = user_data.get(user_id, {}).get('lang', 'uz')

    if not is_ramadan():
        text = translations[lang]['not_ramadan']
    else:
        progress = get_ramadan_progress()
        if progress:
            day, left, end_date = progress
            text = translations[lang]['ramadan_progress'].format(
                day=day, left=left, end_date=end_date
            )
        else:
            text = translations[lang]['not_ramadan']

    keyboard = [[InlineKeyboardButton(
        translations[lang]['back_button'],
        callback_data='back_to_menu'
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)


async def handle_fasting_start(query):
    """Handle fasting start dua"""
    chat_id = query.message.chat_id
    user_id = str(chat_id)
    lang = user_data.get(user_id, {}).get('lang', 'uz')

    if not is_ramadan():
        keyboard = [[InlineKeyboardButton(
            translations[lang]['back_button'],
            callback_data='back_to_menu'
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=translations[lang]['not_ramadan'],
            reply_markup=reply_markup
        )
        return

    dua = translations[lang]['fasting_start_dua']
    image_path = generate_dua_image(dua, lang)

    try:
        with open(image_path, 'rb') as photo:
            media = InputMediaPhoto(photo)
            keyboard = [[InlineKeyboardButton(
                translations[lang]['back_button'],
                callback_data='back_to_menu'
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_media(media=media, reply_markup=reply_markup)
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


async def handle_fasting_end(query):
    """Handle fasting end dua"""
    chat_id = query.message.chat_id
    user_id = str(chat_id)
    lang = user_data.get(user_id, {}).get('lang', 'uz')

    if not is_ramadan():
        keyboard = [[InlineKeyboardButton(
            translations[lang]['back_button'],
            callback_data='back_to_menu'
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=translations[lang]['not_ramadan'],
            reply_markup=reply_markup
        )
        return

    dua = translations[lang]['fasting_end_dua']
    image_path = generate_dua_image(dua, lang)

    try:
        with open(image_path, 'rb') as photo:
            media = InputMediaPhoto(photo)
            keyboard = [[InlineKeyboardButton(
                translations[lang]['back_button'],
                callback_data='back_to_menu'
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_media(media=media, reply_markup=reply_markup)
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


async def handle_next_prayer(query):
    """Handle next prayer time request"""
    chat_id = query.message.chat_id
    user_id = str(chat_id)
    lang = user_data.get(user_id, {}).get('lang', 'uz')
    city_key = user_data.get(user_id, {}).get('city', 'tashkent')

    timings = await get_prayer_times(city_key)
    prayer, p_time = get_next_prayer(timings)
    remaining = calculate_remaining_time(p_time)

    prayer_name = translations[lang]['prayers'][prayer]
    title = translations[lang]['next_prayer_title']

    image_path = generate_next_prayer_image(
        title, prayer_name, p_time, remaining, lang
    )

    try:
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
            message = await query.edit_message_media(
                media=media,
                reply_markup=reply_markup
            )
            user_data[user_id]['next_prayer_msg'] = message.message_id
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


async def handle_update_prayer(query):
    """Handle update prayer time image"""
    await handle_next_prayer(query)
    try:
        await query.answer("✅ Yangilandi")
    except Exception:
        pass


async def handle_update_iftar(query):
    """Handle update iftar time image"""
    await handle_iftar(query)
    try:
        await query.answer("✅ Yangilandi")
    except Exception:
        pass


async def handle_back_to_menu(query, chat_id):
    """Handle back to menu button"""
    user_id = str(chat_id)
    lang = user_data.get(user_id, {}).get('lang', 'uz')
    text = translations[lang]['menu_msg']

    keyboard = [
        [InlineKeyboardButton(
            translations[lang]['next_prayer_button'],
            callback_data='next_prayer'
        )],
        [InlineKeyboardButton(
            translations[lang]['ramadan_button'],
            callback_data='ramadan'
        )],
    ]

    if is_ramadan():
        keyboard.insert(0, [InlineKeyboardButton(
            translations[lang]['iftar_button'],
            callback_data='iftar'
        )])
        keyboard.extend([
            [InlineKeyboardButton(
                translations[lang]['fasting_start_button'],
                callback_data='fasting_start'
            )],
            [InlineKeyboardButton(
                translations[lang]['fasting_end_button'],
                callback_data='fasting_end'
            )],
        ])

    keyboard.append([InlineKeyboardButton(
        translations[lang]['change_city_button'],
        callback_data='change_city'
    )])

    if is_admin(chat_id):
        keyboard.append([InlineKeyboardButton(
            '👨‍💻 Admin Panel',
            callback_data='admin_panel'
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        message = await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
        user_data[user_id]['menu_msg'] = message.message_id
    except BadRequest:
        # If message is media, send new message
        message = await query.message.reply_text(
            text=text,
            reply_markup=reply_markup
        )
        user_data[user_id]['menu_msg'] = message.message_id


# Admin handlers (continued in next part due to length)
async def handle_admin_panel(query, chat_id):
    """Handle admin panel"""
    if not is_admin(chat_id):
        await query.answer("⛔ Siz admin emassiz!")
        return

    # Reset awaiting_ad state
    user_id = str(chat_id)
    if user_id in user_data:
        user_data[user_id].pop('awaiting_ad', None)

    total_users = len([uid for uid in user_data if uid.isdigit()])
    today = get_local_datetime().date().isoformat()
    active_today = sum(
        1 for u in user_data.values()
        if isinstance(u.get('last_seen'), str) and u['last_seen'].startswith(today)
    )

    text = f"""<b>👨‍💻 Admin Panel</b>

📊 Bot boshqaruv paneliga xush kelibsiz!

📈 <b>Statistika:</b>
• 👥 Jami foydalanuvchilar: {total_users} ta
• 🟢 Bugungi faollar: {active_today} ta

Quyidagi bo'limlardan birini tanlang:"""

    keyboard = [
        [InlineKeyboardButton(
            "📊 Foydalanuvchilar statistikasi",
            callback_data='user_stats'
        )],
        [InlineKeyboardButton(
            "🌍 Foydalanuvchilar manzillari",
            callback_data='user_locations'
        )],
        [InlineKeyboardButton(
            "📢 Reklama yuborish",
            callback_data='send_ad'
        )],
        [InlineKeyboardButton(
            "🗑️ Reklamani o'chirish",
            callback_data='delete_ad'
        )],
        [InlineKeyboardButton(
            "⚙️ Sozlamalar",
            callback_data='admin_settings'
        )],
        [InlineKeyboardButton(
            "🔙 Asosiy menyu",
            callback_data='back_to_menu'
        )],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except BadRequest:
        await query.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


async def handle_user_stats(query, chat_id):
    """Handle user statistics"""
    if not is_admin(chat_id):
        await query.answer("⛔ Siz admin emassiz!")
        return

    total_users = len([uid for uid in user_data if uid.isdigit()])
    today = get_local_datetime().date().isoformat()

    active_today = sum(
        1 for u in user_data.values()
        if isinstance(u.get('last_seen'), str) and u['last_seen'].startswith(today)
    )

    text = f"""<b>📊 Foydalanuvchilar Statistikasi</b>

• 👥 Jami foydalanuvchilar: {total_users} ta
• 🟢 Bugungi faollar: {active_today} ta"""

    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def handle_user_locations(query, chat_id):
    """Handle user locations"""
    if not is_admin(chat_id):
        await query.answer("⛔ Siz admin emassiz!")
        return

    locations = {}
    for uid, data in user_data.items():
        if not uid.isdigit():
            continue
        city = data.get('city', 'Noma\'lum')
        locations[city] = locations.get(city, 0) + 1

    text = "<b>🌍 Foydalanuvchilar manzillari</b>\n\n"
    for city, count in sorted(locations.items(), key=lambda x: x[1], reverse=True):
        city_name = CITIES.get(city, {}).get('name', city)
        text += f"• {city_name}: {count} ta\n"

    keyboard = [
        [InlineKeyboardButton("🔄 Yangilash", callback_data='user_locations')],
        [InlineKeyboardButton("🔙 Orqaga", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def handle_send_ad(query, chat_id):
    """Handle send advertisement"""
    if not is_admin(chat_id):
        await query.answer("⛔ Siz admin emassiz!")
        return

    user_data[str(chat_id)]['awaiting_ad'] = True
    save_user_data(user_data)

    text = """<b>📢 Reklama yuborish</b>

Quyidagilardan birini yuboring:
• Matn
• Rasm (caption bilan)
• Video (caption bilan)

Barcha foydalanuvchilarga yuboriladi."""

    keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except BadRequest:
        await query.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )


async def handle_delete_ad(query, chat_id, context):
    """Handle delete advertisement"""
    if not is_admin(chat_id):
        await query.answer("⛔ Siz admin emassiz!")
        return

    deleted_count = 0
    for uid, data in user_data.items():
        if 'ad_msg' in data:
            try:
                await context.bot.delete_message(
                    chat_id=uid,
                    message_id=data['ad_msg']
                )
                del data['ad_msg']
                deleted_count += 1
            except Exception:
                pass

    save_user_data(user_data)

    await query.edit_message_text(
        text=f"✅ Reklama o'chirildi ({deleted_count} ta)",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Orqaga", callback_data='admin_panel')
        ]])
    )


async def handle_admin_settings(query, chat_id):
    """Handle admin settings"""
    if not is_admin(chat_id):
        await query.answer("⛔ Siz admin emassiz!")
        return

    text = """<b>⚙️ Admin Sozlamalari</b>

Quyidagi sozlamalarni o'zgartirishingiz mumkin:"""

    keyboard = [
        [InlineKeyboardButton(
            "🔔 Xabarnomalarni sozlash",
            callback_data='notif_settings'
        )],
        [InlineKeyboardButton("🔙 Orqaga", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def handle_notif_settings(query, chat_id):
    """Handle notification settings"""
    if not is_admin(chat_id):
        await query.answer("⛔ Siz admin emassiz!")
        return

    notif_settings = user_data.get('notif_settings', {})
    suhoor_before = notif_settings.get('suhoor_before', 30)
    iftar_before = notif_settings.get('iftar_before', 10)
    prayer_notifs = notif_settings.get('prayer_notifs', True)

    status = '✅ Yoqilgan' if prayer_notifs else '❌ O\'chirilgan'

    text = f"""<b>🔔 Xabarnoma Sozlamalari</b>

🕒 Saharlik xabarnomasi: {suhoor_before} daqiqa oldin
🌅 Iftorlik xabarnomasi: {iftar_before} daqiqa oldin
🕌 Namoz xabarnomalari: {status}"""

    keyboard = [
        [
            InlineKeyboardButton("🕒 Saharlik", callback_data='set_suhoor_time'),
            InlineKeyboardButton("🌅 Iftorlik", callback_data='set_iftar_time')
        ],
        [InlineKeyboardButton(
            f"🕌 Namoz: {'✅' if prayer_notifs else '❌'}",
            callback_data='toggle_prayer_notifs'
        )],
        [InlineKeyboardButton("🔙 Orqaga", callback_data='admin_settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def handle_set_suhoor_time(query):
    """Handle set suhoor time"""
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


async def handle_set_iftar_time(query):
    """Handle set iftar time"""
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


async def handle_set_suhoor(query, data):
    """Handle set suhoor minutes"""
    minutes = int(data.split('_')[-1])

    if 'notif_settings' not in user_data:
        user_data['notif_settings'] = {}

    user_data['notif_settings']['suhoor_before'] = minutes
    save_user_data(user_data)

    await query.answer(f"✅ Saharlikdan {minutes} daqiqa oldin xabar yuboriladi")

    # Return to notification settings
    chat_id = query.message.chat_id
    await handle_notif_settings(query, chat_id)


async def handle_set_iftar(query, data):
    """Handle set iftar minutes"""
    minutes = int(data.split('_')[-1])

    if 'notif_settings' not in user_data:
        user_data['notif_settings'] = {}

    user_data['notif_settings']['iftar_before'] = minutes
    save_user_data(user_data)

    await query.answer(f"✅ Iftorlikdan {minutes} daqiqa oldin xabar yuboriladi")

    # Return to notification settings
    chat_id = query.message.chat_id
    await handle_notif_settings(query, chat_id)


async def handle_toggle_prayer_notifs(query):
    """Handle toggle prayer notifications"""
    if 'notif_settings' not in user_data:
        user_data['notif_settings'] = {}

    current = user_data['notif_settings'].get('prayer_notifs', True)
    user_data['notif_settings']['prayer_notifs'] = not current
    save_user_data(user_data)

    status = 'yoqildi' if not current else "o'chirildi"
    await query.answer(f"✅ Namoz vaqti xabarnomalari {status}")

    # Refresh the notification settings page
    chat_id = query.message.chat_id
    await handle_notif_settings(query, chat_id)


async def handle_message(update, context):
    """Handle text messages (mainly for admin broadcast)"""
    chat_id = update.effective_chat.id
    user_id = str(chat_id)

    await update_user_activity(chat_id)

    # Check if admin is sending broadcast
    if user_id in user_data and user_data[user_id].get('awaiting_ad') and is_admin(chat_id):
        await send_broadcast(update, context)
        return

    # Regular message handling (if needed)
    # For now, we don't respond to regular messages
    pass


async def send_broadcast(update, context):
    """Send broadcast message to all users"""
    chat_id = update.effective_chat.id
    user_id = str(chat_id)

    # Count total users (excluding admin)
    total_users = len([uid for uid in user_data.keys() if uid.isdigit() and uid != user_id])

    # Send processing message
    status_msg = await update.message.reply_text(
        f"⏳ Reklama yuborilmoqda...\nJami: {total_users} ta foydalanuvchi"
    )

    sent_count = 0
    error_count = 0
    blocked_count = 0

    # Prepare caption
    caption = update.message.caption or update.message.text or ""

    # Add signature if not present
    if not any(word in caption.lower() for word in ['@', 'kanal', 'bot']):
        caption += "\n\n📱 @Ramazon_va_Namoz_bot"

    # Send to all users
    for target_user_id in user_data:
        if not target_user_id.isdigit() or target_user_id == user_id:
            continue

        try:
            # Handle different message types
            if update.message.photo:
                photo = update.message.photo[-1]
                await context.bot.send_photo(
                    chat_id=target_user_id,
                    photo=photo.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif update.message.video:
                video = update.message.video
                await context.bot.send_video(
                    chat_id=target_user_id,
                    video=video.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif update.message.document:
                document = update.message.document
                await context.bot.send_document(
                    chat_id=target_user_id,
                    document=document.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif update.message.text:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=caption,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                )

            sent_count += 1

            # Update progress every 10 messages
            if sent_count % 10 == 0:
                try:
                    await status_msg.edit_text(
                        f"⏳ Reklama yuborilmoqda...\n"
                        f"✅ Yuborildi: {sent_count}/{total_users}\n"
                        f"❌ Xatolik: {error_count}\n"
                        f"🚫 Bloklangan: {blocked_count}"
                    )
                except Exception:
                    pass

        except Forbidden:
            blocked_count += 1
            logger.info(f"User {target_user_id} blocked the bot")
        except TelegramError as e:
            error_count += 1
            logger.error(f"Telegram error sending to {target_user_id}: {e}")
        except Exception as e:
            error_count += 1
            logger.error(f"Error sending to {target_user_id}: {e}")

    # Clean up
    user_data[user_id].pop('awaiting_ad', None)
    save_user_data(user_data)

    # Send completion message
    await status_msg.edit_text(
        f"✅ <b>Reklama yuborish yakunlandi!</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"• 🔢 Jami: {total_users} ta\n"
        f"• ✅ Muvaffaqiyatli: {sent_count}\n"
        f"• ❌ Xatolik: {error_count}\n"
        f"• 🚫 Bloklangan: {blocked_count}",
        parse_mode='HTML'
    )


async def send_menu(chat_id, bot=None, update_existing=False):
    """Send or update menu for a user (used by scheduler)"""
    if bot is None:
        bot = Bot(token=BOT_TOKEN)

    user_id = str(chat_id)
    lang = user_data.get(user_id, {}).get('lang', 'uz')
    text = translations[lang]['menu_msg']

    keyboard = [
        [InlineKeyboardButton(
            translations[lang]['next_prayer_button'],
            callback_data='next_prayer'
        )],
        [InlineKeyboardButton(
            translations[lang]['ramadan_button'],
            callback_data='ramadan'
        )],
    ]

    if is_ramadan():
        keyboard.insert(0, [InlineKeyboardButton(
            translations[lang]['iftar_button'],
            callback_data='iftar'
        )])
        keyboard.extend([
            [InlineKeyboardButton(
                translations[lang]['fasting_start_button'],
                callback_data='fasting_start'
            )],
            [InlineKeyboardButton(
                translations[lang]['fasting_end_button'],
                callback_data='fasting_end'
            )],
        ])

    keyboard.append([InlineKeyboardButton(
        translations[lang]['change_city_button'],
        callback_data='change_city'
    )])

    if is_admin(chat_id):
        keyboard.append([InlineKeyboardButton(
            '👨‍💻 Admin Panel',
            callback_data='admin_panel'
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if update_existing and 'menu_msg' in user_data.get(user_id, {}):
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=user_data[user_id]['menu_msg'],
                    text=text,
                    reply_markup=reply_markup
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    # If edit fails, send new message
                    message = await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup
                    )
                    user_data[user_id]['menu_msg'] = message.message_id
                    save_user_data(user_data)
        else:
            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id]['menu_msg'] = message.message_id
            save_user_data(user_data)

    except Forbidden:
        logger.info(f"User {chat_id} blocked the bot")
    except TelegramError as e:
        logger.error(f"Error sending menu to {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in send_menu for {chat_id}: {e}", exc_info=True)


async def admin_command(update, context):
    """Handle /admin command"""
    chat_id = update.effective_chat.id

    if not is_admin(chat_id):
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    # Reset awaiting_ad state
    user_id = str(chat_id)
    if user_id in user_data:
        user_data[user_id].pop('awaiting_ad', None)

    total_users = len([uid for uid in user_data if uid.isdigit()])
    today = get_local_datetime().date().isoformat()
    active_today = sum(
        1 for u in user_data.values()
        if isinstance(u.get('last_seen'), str) and u['last_seen'].startswith(today)
    )

    text = f"""<b>👨‍💻 Admin Panel</b>

📊 Bot boshqaruv paneliga xush kelibsiz!

📈 <b>Statistika:</b>
• 👥 Jami foydalanuvchilar: {total_users} ta
• 🟢 Bugungi faollar: {active_today} ta

Quyidagi bo'limlardan birini tanlang:"""

    keyboard = [
        [InlineKeyboardButton(
            "📊 Foydalanuvchilar statistikasi",
            callback_data='user_stats'
        )],
        [InlineKeyboardButton(
            "🌍 Foydalanuvchilar manzillari",
            callback_data='user_locations'
        )],
        [InlineKeyboardButton(
            "📢 Reklama yuborish",
            callback_data='send_ad'
        )],
        [InlineKeyboardButton(
            "🗑️ Reklamani o'chirish",
            callback_data='delete_ad'
        )],
        [InlineKeyboardButton(
            "⚙️ Sozlamalar",
            callback_data='admin_settings'
        )],
        [InlineKeyboardButton(
            "🔙 Asosiy menyu",
            callback_data='back_to_menu'
        )],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except BadRequest:
            await update.callback_query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
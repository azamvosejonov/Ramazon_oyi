import os
import logging

logger = logging.getLogger(__name__)

# ==================== Bot Configuration ====================

# Bot token (required)
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Admin ID (optional but recommended)
ADMIN_ID = os.getenv('ADMIN_ID')
if not ADMIN_ID:
    logger.warning("ADMIN_ID not set - admin features will be disabled")

# Global chat ID (optional, legacy support)
CHAT_ID = os.getenv('CHAT_ID')

# Azan audio URL (optional)
AZAN_AUDIO_URL = os.getenv(
    'AZAN_AUDIO_URL',
    'https://www.myinstants.com/en/instant/azan-9059/?utm_source=copy&utm_medium=share'
)

# ==================== Cities Configuration ====================

CITIES = {
    'tashkent': {
        'name': 'Toshkent shahri',
        'country': 'uzbekistan',
        'api_name': 'Tashkent',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Tashkent'
    },
    'samarkand': {
        'name': 'Samarqand shahri',
        'country': 'uzbekistan',
        'api_name': 'Samarkand',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Samarkand'
    },
    'bukhara': {
        'name': 'Buxoro shahri',
        'country': 'uzbekistan',
        'api_name': 'Bukhara',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Samarkand'
    },
    'khiva': {
        'name': 'Xiva shahri',
        'country': 'uzbekistan',
        'api_name': 'Khiva',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Samarkand'
    },
    'andijan': {
        'name': 'Andijon shahri',
        'country': 'uzbekistan',
        'api_name': 'Andijan',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Tashkent'
    },
    'namangan': {
        'name': 'Namangan shahri',
        'country': 'uzbekistan',
        'api_name': 'Namangan',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Tashkent'
    },
    'ferghana': {
        'name': "Farg'ona shahri",
        'country': 'uzbekistan',
        'api_name': 'Fergana',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Tashkent'
    },
    'nukus': {
        'name': 'Nukus shahri',
        'country': 'uzbekistan',
        'api_name': 'Nukus',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Samarkand'
    },
    'urgench': {
        'name': 'Urganch shahri',
        'country': 'uzbekistan',
        'api_name': 'Urgench',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Samarkand'
    },
    'navoi': {
        'name': 'Navoiy shahri',
        'country': 'uzbekistan',
        'api_name': 'Navoi',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Samarkand'
    },
    'jizzakh': {
        'name': 'Jizzax shahri',
        'country': 'uzbekistan',
        'api_name': 'Jizzakh',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Tashkent'
    },
    'gulistan': {
        'name': 'Guliston shahri',
        'country': 'uzbekistan',
        'api_name': 'Gulistan',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Tashkent'
    },
    'termez': {
        'name': 'Termiz shahri',
        'country': 'uzbekistan',
        'api_name': 'Termez',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Samarkand'
    },
    'karshi': {
        'name': 'Qarshi shahri',
        'country': 'uzbekistan',
        'api_name': 'Karshi',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Samarkand'
    },
    'margilan': {
        'name': "Marg'ilon shahri",
        'country': 'uzbekistan',
        'api_name': 'Margilan',
        'api_country': 'Uzbekistan',
        'timezone': 'Asia/Tashkent'
    }
}

# ==================== Translations ====================

translations = {
    'uz': {
        # Start & Setup
        'start_msg': "🌙 Assalomu alaykum!\n\nRamazon va Namoz botiga xush kelibsiz.\n\n🌍 Tilni tanlang:",
        'confirmation': "✅ Til tanlandi: O'zbek",
        'select_country': "🌍 Iltimos, mamlakatni tanlang:",
        'select_city': "📍 Iltimos, shaharni tanlang:",
        'city_selected': "✅ Shahar tanlandi: {city}\n\nEndi siz barcha xizmatlardan foydalanishingiz mumkin!",

        # Menu
        'menu_msg': "📱 Asosiy menyu\n\nQuyidagi bo'limlardan birini tanlang:",

        # Prayer Times
        'next_prayer': "🕌 Keyingi namoz:\n\n{prayer}\n⏰ Vaqt: {time}\n⏳ Qolgan: {remaining}",
        'next_prayer_title': "Keyingi Namoz Vaqti",
        'prayer_times': "🕌 Bugungi namoz vaqtlari ({city}):\n\n🌄 Bomdod: {fajr}\n☀️ Peshin: {dhuhr}\n🌤️ Asr: {asr}\n🌅 Shom: {maghrib}\n🌙 Xufton: {isha}",
        'prayer_notification': "🕌 {prayer} namoz vaqti keldi!\n\nAlloh sizning namozingizni qabul qilsin!",

        # Ramadan
        'ramadan_progress': "🌙 Ramazon muborak!\n\n📅 {day}-kun\n⏳ Qolgan kunlar: {left}\n📆 Tugash sanasi: {end_date}",
        'not_ramadan': "🌙 Hozir Ramazon oyi emas.\n\nIltimos, Ramazon oyida qaytadan urinib ko'ring.",

        # Fasting
        'fasting_start': "🌅 Ro'za boshlash vaqti keldi!\n\n🤲 Niyat:\n{dua}",
        'fasting_end': "🌇 Ro'za ochish vaqti!\n\n🤲 Duo:\n{dua}",
        'fasting_start_dua': "Navvaytu an asuma sovma shahri romazona minal fajri ilal mag'ribi, xolisan lillahi ta'ala. Allohu Akbar!",
        'fasting_end_dua': "Allohumma laka sumtu va bika amantu va 'ala rizqika aftartu va 'alayka tavakkaltu, fag'firli ma qoddamtu va ma axxortu. Birrohmannar rohim.",

        # Iftar/Suhoor
        'iftar_remaining': "🕰️ Iftorga qolgan vaqt: {time}",
        'early_iftar': "🕰️ Iftorga 2 daqiqa qoldi!\n\nTayyorgarlik ko'ring va duo qiling.",
        'early_sahur': "🌙 Saharlikka 30 daqiqa qoldi!\n\nUyg'oning va saharlik yeying!",
        'late_fasting_start': "⏰ Ro'za boshlash vaqti o'tib ketdi.\n\nErtaga erta tursangiz bo'ladi inshAlloh.",

        # Buttons
        'iftar_button': "🕰️ Iftorga qolgan vaqt",
        'next_prayer_button': "🕌 Keyingi namoz",
        'ramadan_button': "🌙 Ramazon ma'lumotlari",
        'change_city_button': "📍 Shaharni o'zgartirish",
        'back_button': "🔙 Orqaga",
        'update_button': "🔄 Yangilash",
        'fasting_start_button': "🌅 Ro'za boshlash duosi",
        'fasting_end_button': "🌇 Ro'za ochish duosi",

        # Prayer Names
        'prayers': {
            'Fajr': '🌄 Bomdod',
            'Dhuhr': '☀️ Peshin',
            'Asr': '🌤️ Asr',
            'Maghrib': '🌅 Shom',
            'Isha': '🌙 Xufton'
        },

        # Azan
        'azan': "🕌 Azon:\n\nAllohu Akbar! Allohu Akbar!\nAshhadu alla ilaha illallah!\nAshhadu anna Muhammadur rasulullah!\nHayya alas-salah!\nHayya alal-falah!\nAllohu Akbar! La ilaha illallah!"
    },

    'en': {
        # Start & Setup
        'start_msg': "🌙 Assalamu Alaikum!\n\nWelcome to Ramadan & Prayer Times Bot.\n\n🌍 Choose your language:",
        'confirmation': "✅ Language selected: English",
        'select_country': "🌍 Please select your country:",
        'select_city': "📍 Please select your city:",
        'city_selected': "✅ City selected: {city}\n\nYou can now use all features!",

        # Menu
        'menu_msg': "📱 Main Menu\n\nSelect one of the options below:",

        # Prayer Times
        'next_prayer': "🕌 Next Prayer:\n\n{prayer}\n⏰ Time: {time}\n⏳ Remaining: {remaining}",
        'next_prayer_title': "Next Prayer Time",
        'prayer_times': "🕌 Today's prayer times ({city}):\n\n🌄 Fajr: {fajr}\n☀️ Dhuhr: {dhuhr}\n🌤️ Asr: {asr}\n🌅 Maghrib: {maghrib}\n🌙 Isha: {isha}",
        'prayer_notification': "🕌 It's time for {prayer} prayer!\n\nMay Allah accept your prayer!",

        # Ramadan
        'ramadan_progress': "🌙 Ramadan Mubarak!\n\n📅 Day {day}\n⏳ Days remaining: {left}\n📆 End date: {end_date}",
        'not_ramadan': "🌙 It's not Ramadan month.\n\nPlease try again during Ramadan.",

        # Fasting
        'fasting_start': "🌅 Time to start fasting!\n\n🤲 Intention:\n{dua}",
        'fasting_end': "🌇 Time to break your fast!\n\n🤲 Dua:\n{dua}",
        'fasting_start_dua': "Nawaitu sawma ghadin 'an shahri Ramadan min al-fajri ila al-maghribi, khalisan lillahi ta'ala. Allahu Akbar!",
        'fasting_end_dua': "Allahumma laka sumtu wa bika amantu wa 'ala rizqika aftartu wa 'alayka tawakkaltu, faghfir li ma qaddamtu wa ma akhkhartu. Birrahmanir Rahim.",

        # Iftar/Suhoor
        'iftar_remaining': "🕰️ Time until Iftar: {time}",
        'early_iftar': "🕰️ 2 minutes until Iftar!\n\nGet ready and make dua.",
        'early_sahur': "🌙 30 minutes until Suhoor ends!\n\nWake up and eat Suhoor!",
        'late_fasting_start': "⏰ Fasting start time has passed.\n\nTry waking up earlier tomorrow inshAllah.",

        # Buttons
        'iftar_button': "🕰️ Time to Iftar",
        'next_prayer_button': "🕌 Next Prayer",
        'ramadan_button': "🌙 Ramadan Info",
        'change_city_button': "📍 Change City",
        'back_button': "🔙 Back",
        'update_button': "🔄 Update",
        'fasting_start_button': "🌅 Start Fasting Dua",
        'fasting_end_button': "🌇 Break Fast Dua",

        # Prayer Names
        'prayers': {
            'Fajr': '🌄 Fajr',
            'Dhuhr': '☀️ Dhuhr',
            'Asr': '🌤️ Asr',
            'Maghrib': '🌅 Maghrib',
            'Isha': '🌙 Isha'
        },

        # Azan
        'azan': "🕌 Adhan:\n\nAllahu Akbar! Allahu Akbar!\nAshhadu alla ilaha illallah!\nAshhadu anna Muhammadar rasulullah!\nHayya 'ala-s-salah!\nHayya 'ala-l-falah!\nAllahu Akbar! La ilaha illallah!"
    },

    'ru': {
        # Start & Setup
        'start_msg': "🌙 Ассаляму алейкум!\n\nДобро пожаловать в бот Рамадан и Времена намазов.\n\n🌍 Выберите язык:",
        'confirmation': "✅ Язык выбран: Русский",
        'select_country': "🌍 Пожалуйста, выберите страну:",
        'select_city': "📍 Пожалуйста, выберите город:",
        'city_selected': "✅ Город выбран: {city}\n\nТеперь вы можете использовать все функции!",

        # Menu
        'menu_msg': "📱 Главное меню\n\nВыберите один из разделов:",

        # Prayer Times
        'next_prayer': "🕌 Следующий намаз:\n\n{prayer}\n⏰ Время: {time}\n⏳ Осталось: {remaining}",
        'next_prayer_title': "Следующий Намаз",
        'prayer_times': "🕌 Время намазов на сегодня ({city}):\n\n🌄 Фаджр: {fajr}\n☀️ Зухр: {dhuhr}\n🌤️ Аср: {asr}\n🌅 Магриб: {maghrib}\n🌙 Иша: {isha}",
        'prayer_notification': "🕌 Время намаза {prayer}!\n\nДа примет Аллах ваш намаз!",

        # Ramadan
        'ramadan_progress': "🌙 Рамадан Мубарак!\n\n📅 {day}-й день\n⏳ Осталось дней: {left}\n📆 Дата окончания: {end_date}",
        'not_ramadan': "🌙 Сейчас не месяц Рамадан.\n\nПопробуйте снова во время Рамадана.",

        # Fasting
        'fasting_start': "🌅 Время начать пост!\n\n🤲 Намерение:\n{dua}",
        'fasting_end': "🌇 Время разговения!\n\n🤲 Дуа:\n{dua}",
        'fasting_start_dua': "Навайту ан асума саума шаҳри Рамазона миналь-фаджри иляль-магриби, холисан лилляхи тааля. Аллаху Акбар!",
        'fasting_end_dua': "Аллахумма лякя сумту ва бикя аманту ва 'аля ризкыкя афтарту ва 'аляйкя таваккальту, фагфирли ма каддамту ва ма аххарту. Биррахманир-Рахим.",

        # Iftar/Suhoor
        'iftar_remaining': "🕰️ До ифтара: {time}",
        'early_iftar': "🕰️ До ифтара 2 минуты!\n\nГотовьтесь и читайте дуа.",
        'early_sahur': "🌙 До сухура осталось 30 минут!\n\nПросыпайтесь и ешьте сухур!",
        'late_fasting_start': "⏰ Время начала поста прошло.\n\nПостарайтесь проснуться раньше завтра иншаАллах.",

        # Buttons
        'iftar_button': "🕰️ До ифтара",
        'next_prayer_button': "🕌 Следующий намаз",
        'ramadan_button': "🌙 О Рамадане",
        'change_city_button': "📍 Изменить город",
        'back_button': "🔙 Назад",
        'update_button': "🔄 Обновить",
        'fasting_start_button': "🌅 Дуа начала поста",
        'fasting_end_button': "🌇 Дуа разговения",

        # Prayer Names
        'prayers': {
            'Fajr': '🌄 Фаджр',
            'Dhuhr': '☀️ Зухр',
            'Asr': '🌤️ Аср',
            'Maghrib': '🌅 Магриб',
            'Isha': '🌙 Иша'
        },

        # Azan
        'azan': "🕌 Азан:\n\nАллаху Акбар! Аллаху Акбар!\nАшхаду алля иляха илляллах!\nАшхаду анна Мухаммадар-расулюллах!\nХаййа 'аля-с-саля!\nХаййя 'аля-ль-фалях!\nАллаху Акбар! Ля иляха илляллах!"
    }
}

# ==================== Helper Functions ====================

def get_city_info(city_key: str) -> dict:
    """Get city information by key"""
    return CITIES.get(city_key, CITIES['tashkent'])


def get_translation(lang: str, key: str, **kwargs) -> str:
    """Get translation with formatting"""
    try:
        text = translations.get(lang, translations['uz']).get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text
    except KeyError:
        logger.error(f"Translation key not found: {key} for language: {lang}")
        return key
    except Exception as e:
        logger.error(f"Error formatting translation {key}: {e}")
        return key


def get_supported_languages() -> list:
    """Get list of supported languages"""
    return list(translations.keys())


def validate_config() -> bool:
    """Validate configuration"""
    errors = []

    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is not set")

    if not CITIES:
        errors.append("No cities configured")

    if not translations:
        errors.append("No translations configured")

    # Check if all languages have required keys
    required_keys = ['start_msg', 'menu_msg', 'prayers']
    for lang, trans in translations.items():
        for key in required_keys:
            if key not in trans:
                errors.append(f"Missing key '{key}' in {lang} translations")

    if errors:
        for error in errors:
            logger.error(f"Config validation error: {error}")
        return False

    return True


# Validate config on import
if __name__ != "__main__":
    if not validate_config():
        logger.warning("Configuration validation failed")
    else:
        logger.info("Configuration validated successfully")
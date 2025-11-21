import os

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable kerak")

# Global chat_id, agar kerak bo'lsa
CHAT_ID = os.getenv('CHAT_ID')

# Cities
CITIES = {
    # Shaharlar - Faqat O'zbekiston shaharlari
    'tashkent': {'name': 'Toshkent shahri', 'country': 'uzbekistan'},
    'samarkand': {'name': 'Samarqand shahri', 'country': 'uzbekistan'},
    'bukhara': {'name': 'Buxoro shahri', 'country': 'uzbekistan'},
    'khiva': {'name': 'Xiva shahri', 'country': 'uzbekistan'},
    'andijan': {'name': 'Andijon shahri', 'country': 'uzbekistan'},
    'namangan': {'name': 'Namangan shahri', 'country': 'uzbekistan'},
    'ferghana': {'name': 'Farg\'ona shahri', 'country': 'uzbekistan'},
    'nukus': {'name': 'Nukus shahri', 'country': 'uzbekistan'},
    'urgench': {'name': 'Urganch shahri', 'country': 'uzbekistan'},
    'navoi': {'name': 'Navoiy shahri', 'country': 'uzbekistan'},
    'jizzakh': {'name': 'Jizzax shahri', 'country': 'uzbekistan'},
    'gulistan': {'name': 'Guliston shahri', 'country': 'uzbekistan'},
    'termez': {'name': 'Termiz shahri', 'country': 'uzbekistan'},
    'karshi': {'name': 'Qarshi shahri', 'country': 'uzbekistan'},
    'margilan': {'name': 'Marg\'ilon shahri', 'country': 'uzbekistan'}
}

# Tarjimalar
translations = {
    'uz': {
        'start_msg': "Tilni tanlang:",
        'confirmation': "Til tanlandi: O'zbek",
        'select_country': "Iltimos, mamlakatni tanlang:",
        'select_city': "Iltimos, shaharni tanlang:",
        'menu_msg': "Nima ko'rmoqchisiz? ",
        'iftar_remaining': " Iftorga qolgan vaqt: {time}",
        'next_prayer': " Keyingi namoz:\n\n {prayer}\n Vaqt: {time}\n Qolgan: {remaining}",
        'next_prayer_title': "Keyingi Namoz",
        'ramadan_progress': " Ramazon: {day}-kun, qolgan kunlar: {left}, tugash sanasi: {end_date}",
        'fasting_start': " Ro'za boshlash vaqti keldi!\n{dua}",
        'fasting_end': " Ro'za ochish vaqti!\n{dua}",
        'prayer_times': " Bugungi namoz vaqtlari ({city}):\nBomdod: {fajr}\nPeshin: {dhuhr}\nAsr: {asr}\nShom: {maghrib}\nXufton: {isha}",
        'fasting_start_dua': "Navvaytu an asuma sovma shahri romazona minal fajri ilal mag'ribi, xolisan lillahi ta'ala. Allohu Akbar!",
        'fasting_end_dua': "Allohumma laka sumtu va bika amantu va 'ala rizqika aftartu va 'alayka tavakkaltu, fag'firli ma qoddamtu va ma axxortu. Birrohmannar rohim.",
        'iftar_button': "🕰 Iftorga qolgan vaqt",
        'next_prayer_button': "🕌 Keyingi namoz",
        'ramadan_button': "🌙 Ramazon ma'lumotlari",
        'change_city_button': "📍 Shaharni o'zgartirish",
        'back_button': "🔙 Orqaga qaytish",
        'update_button': "🔄 Yangilash",
        'fasting_start_button': "🌅 Ro'za boshlash",
        'fasting_end_button': "🌇 Ro'za ochish",
        'not_ramadan': "Hozir Ramazon oyi emas. Iltimos, Ramazon oyida qaytadan urinib ko'ring.",
        'prayers': {
            'Fajr': 'Bomdod ',
            'Dhuhr': 'Peshin ',
            'Asr': 'Asr ',
            'Maghrib': 'Shom ',
            'Isha': 'Xufton '
        },
        'azan': "Allohu Akbar! Allohu Akbar!\nAshhadu alla ilaha illallah!\nAshhadu anna Muhammadur rasulullah!\nHayya alas-salah!\nHayya alal-falah!\nAllohu Akbar! La ilaha illallah!"
    },
    'en': {
        'start_msg': "Choose language:",
        'confirmation': "Language selected: English",
        'select_country': "Please select your country:",
        'select_city': "Please select your city:",
        'menu_msg': "What do you want to see? ",
        'iftar_remaining': " Time remaining to Iftar: {time}",
        'next_prayer': " Next Prayer:\n\n {prayer}\n Time: {time}\n Remaining: {remaining}",
        'next_prayer_title': "Next Prayer",
        'ramadan_progress': " Ramadan: Day {day}, days left: {left}, end date: {end_date}",
        'fasting_start': " Time to start fasting!\n{dua}",
        'fasting_end': " Time to break the fast!\n{dua}",
        'prayer_times': " Today's prayer times ({city}):\nFajr: {fajr}\nDhuhr: {dhuhr}\nAsr: {asr}\nMaghrib: {maghrib}\nIsha: {isha}",
        'fasting_start_dua': "Nawaitu sawma ghadin 'an shahri Ramadan min al-fajri ila al-maghribi, khalisan lillahi ta'ala. Allahu Akbar!",
        'fasting_end_dua': "Allahumma laka sumtu wa bika amantu wa 'ala rizqika aftartu wa 'alayka tawakkaltu, faghfir li ma qaddamtu wa ma akhkhartu. Birrahmanir Rahim.",
        'iftar_button': "🕰 Time to Iftar",
        'next_prayer_button': "🕌 Next Prayer",
        'ramadan_button': "🌙 Ramadan Info",
        'change_city_button': "📍 Change City",
        'back_button': "🔙 Back",
        'update_button': "🔄 Update",
        'fasting_start_button': "🌅 Start Fasting",
        'fasting_end_button': "🌇 Break Fast",
        'not_ramadan': "It's not Ramadan month yet. Please try again during Ramadan.",
        'prayers': {
            'Fajr': 'Fajr ',
            'Dhuhr': 'Dhuhr ',
            'Asr': 'Asr ',
            'Maghrib': 'Maghrib ',
            'Isha': 'Isha '
        },
        'azan': "Allahu Akbar! Allahu Akbar!\nAshhadu alla ilaha illallah!\nAshhadu anna Muhammadar rasulullah!\nHayya 'ala-s-salah!\nHayya 'ala-l-falah!\nAllahu Akbar! La ilaha illallah!"
    },
    'ru': {
        'start_msg': "Выберите язык:",
        'confirmation': "Язык выбран: Русский",
        'select_country': "Пожалуйста, выберите страну:",
        'select_city': "Пожалуйста, выберите город:",
        'menu_msg': "Что вы хотите увидеть? ",
        'iftar_remaining': " Время до разговения: {time}",
        'next_prayer': " Следующий намаз:\n\n {prayer}\n Время: {time}\n Осталось: {remaining}",
        'next_prayer_title': "Следующий Намаз",
        'ramadan_progress': " Рамадан: {day}-день, осталось дней: {left}, дата окончания: {end_date}",
        'fasting_start': " Время начать пост!\n{dua}",
        'fasting_end': " Время разговения!\n{dua}",
        'prayer_times': "🕌 Время намазов на сегодня ({city}):\n🌄 Фаджр: {fajr}\n☀️ Зухр: {dhuhr}\n🌅 Аср: {asr}\n🌇 Магриб: {maghrib}\n🌃 Иша: {isha}",
        'fasting_start_dua': "Навайту ан асума саума шаҳри Рамазона миналь-фаджри иляль-магриби, холисан лилляхи тааля. Аллаху Акбар!",
        'fasting_end_dua': "Аллахумма лякя сумту ва бикя аманту ва 'аля ризкыкя афтарту ва 'аляйкя таваккальту, фагфирли ма каддамту ва ма аххарту. Биррахманир-Рахим.",
        'iftar_button': "🕰 До ифтара",
        'next_prayer_button': "🕌 Следующий намаз",
        'ramadan_button': "🌙 О Рамадане",
        'change_city_button': "📍 Изменить город",
        'back_button': "🔙 Назад",
        'update_button': "🔄 Обновить",
        'fasting_start_button': "🌅 Начать пост",
        'fasting_end_button': "🌇 Разговение",
        'not_ramadan': "Сейчас не месяц Рамадан. Пожалуйста, попробуйте снова во время Рамадана.",
        'prayers': {
            'Fajr': 'Фаджр ',
            'Dhuhr': 'Зухр ',
            'Asr': 'Аср ',
            'Maghrib': 'Магриб ',
            'Isha': 'Иша '
        },
        'azan': "Аллаху Акбар! Аллаху Акбар!\nАшхаду алля иляха илляллах!\nАшхаду анна Мухаммадар-расулюллах!\nХаййа 'аля-с-саля!\nХаййа 'аля-ль-фалях!\nАллаху Акбар! Ля иляха илляллах!"
    }
}

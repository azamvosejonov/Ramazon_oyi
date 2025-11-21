# Ramazon Bot

Bu bot Ramazon oyida ro'za boshlash, ro'za ochish va namoz vaqtlari haqida xabar beradi. Ko'plab tillarni qo'llab-quvvatlaydi: O'zbek, English, Русский, العربية, فارسی.

## Xususiyatlar

- **Avtomatik xabarlar**: Ro'za boshlash, ochish va namoz vaqtlari. Barcha namoz vaqtlarida bildirishnoma, ro'za boshlashdan 1 soat oldin va ochishdan 2 daqiqa oldin eslatma. Ro'za boshlashdan 30 daqiqa keyin kechikkan eslatma.
- **Interaktiv menyu**: /start dan keyin til tanlash, shahar tanlash, keyin iftar vaqtiga qolgan vaqt, keyingi namoz, Ramazon ma'lumotlari ko'rish. Shaharni o'zgartirish imkoni.
- **Real vaqt**: Vaqtlar shahar bo'yicha aniq, real vaqtda yangilanadi.
- **Chiroyli rasm**: Ro'za boshlash va ochish duolarini chiroyli Ramazon rasmlarida yuboradi.
- **Shaharlari**: O'zbekiston (10 shahar), AQSH (10 shahar), Eron (10 shahar), Arab mamlakatlari (Saudi Arabia 10, Egypt 10), Markaziy Osiyo (Kyrgyzstan 10, Tajikistan 10, Turkmenistan 10) shaharlari.

## Fayllar

- `main.py`: Kirish nuqtasi.
- `config.py`: Konfiguratsiya va tarjimalar.
- `handlers.py`: Telegram handler'lari.
- `scheduler.py`: Jadval rejalashtirish.
- `utils.py`: Yordamchi funksiyalar.

## O'rnatish

1. Python 3.11 o'rnating.
2. Kutubxonalarni o'rnating: `pip install -r requirements.txt`

## Ishga tushirish

1. Telegram bot yaratib, token oling: [@BotFather](https://t.me/botfather)
2. Chat ID ni toping (sizning user ID yoki kanal ID).
3. `.env.example` ni `.env` ga nusxalab, qiymatlarni kiriting.
   - `BOT_TOKEN`: Bot token
   - `CHAT_ID`: Chat ID (ixtiyoriy, agar bitta chat uchun)

4. `python main.py` ishga tushiring.

Bot /start bosganda til tanlash tugmalarini ko'rsatadi. Til tanlanganda, menyu tugmalari chiqadi: iftar vaqti, keyingi namoz, Ramazon ma'lumotlari.

## Fayllar

- `main.py`: Kirish nuqtasi.
- `config.py`: Konfiguratsiya va tarjimalar.
- `handlers.py`: Telegram handler'lari.
- `scheduler.py`: Jadval rejalashtirish.
- `utils.py`: Yordamchi funksiyalar.

## Docker bilan

1. `BOT_TOKEN` va `CHAT_ID` environment variable'larni o'rnating yoki `.env` fayl yarating.
2. `docker-compose up --build` ishga tushiring.

Yoki oddiy Docker:

1. `docker build -t ramazon-bot .`
2. `docker run -e BOT_TOKEN=your_token -e CHAT_ID=your_chat_id -v $(pwd)/user_data.json:/app/user_data.json ramazon-bot`

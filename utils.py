import re
import os
import logging
import requests
from datetime import datetime, date, time, timedelta
from hijri_converter import Hijri, Gregorian
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pytz


TIMEZONE_NAME = os.getenv('TIMEZONE', 'Asia/Tashkent')
LOCAL_TIMEZONE = pytz.timezone(TIMEZONE_NAME)

# Logging konfiguratsiyasi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_local_datetime():
    """Mahalliy vaqt zonasida hozirgi vaqtni qaytaradi"""
    return datetime.now(LOCAL_TIMEZONE)


def get_local_time():
    """Mahalliy vaqt zonasida hozirgi vaqtni time obyekti sifatida qaytaradi"""
    return get_local_datetime().time()


def _get_target_datetime(target_time_str, reference_dt=None):
    """Berilgan vaqtga qadar qolgan vaqtni hisoblash uchun target datetime yaratadi"""
    reference_dt = reference_dt or get_local_datetime()
    try:
        h, m = map(int, target_time_str.split(':'))
        target = reference_dt.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= reference_dt:
            target += timedelta(days=1)
        return target
    except (ValueError, AttributeError) as e:
        logger.error(f"Vaqtni parse qilishda xato: {target_time_str}, {e}")
        raise


def get_remaining_timedelta(target_time_str):
    """Berilgan vaqtgacha qolgan vaqtni timedelta sifatida qaytaradi"""
    target_dt = _get_target_datetime(target_time_str)
    now_dt = get_local_datetime()
    return target_dt - now_dt


def strip_emojis(text):
    """Matndan emojilarni olib tashlaydi"""
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002700-\U000027BF"  # dingbats
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)


async def get_prayer_times(city_key):
    """Shahar uchun namoz vaqtlarini API orqali oladi"""
    from config import CITIES

    try:
        city_info = CITIES[city_key]
    except KeyError:
        logger.warning(f"Shahar topilmadi: {city_key}, Toshkentga o'tildi")
        city_info = CITIES['tashkent']  # Fallback to Tashkent

    city = city_info.get('api_name', city_info.get('name'))
    country = city_info.get('api_country', city_info.get('country', 'Uzbekistan'))

    if not city or not country:
        raise ValueError(f"Shahar konfiguratsiyasida maydonlar yetishmayapti: '{city_key}'")

    url = "https://api.aladhan.com/v1/timingsByCity"
    params = {
        'city': city,
        'country': country,
        'method': 2,
        'school': 1,  # Hanafi (Oʻzbekistonda keng tarqalgan)
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"Namoz vaqtlari API xatosi: {e}")
        raise

    try:
        timings = data['data']['timings']
    except (KeyError, TypeError):
        logger.error(f"API kutilmagan ma'lumot qaytardi: {city}/{country}")
        raise ValueError(f"Namoz vaqtlari API kutilmagan ma'lumot qaytardi: {city}/{country}")

    # Vaqtlarni tozalash - vaqt zonasi ma'lumotini olib tashlash (masalan, "05:30 (+05)" -> "05:30")
    cleaned_timings = {}
    for key, value in timings.items():
        if isinstance(value, str) and ' ' in value:
            cleaned_timings[key] = value.split(' ')[0]
        else:
            cleaned_timings[key] = value

    return cleaned_timings


def is_ramadan():
    """Ramazon oyini hijri_converter yordamida dinamik aniqlash"""
    today = date.today()
    try:
        hijri = Gregorian(today.year, today.month, today.day).to_hijri()
        return hijri.month == 9  # Ramazon = 9-oy hijriy taqvimda
    except Exception as e:
        logger.error(f"Ramazon tekshirishda xato: {e}")
        return False


def get_ramadan_progress():
    """Ramazon kunlari progressini hijri_converter yordamida hisoblash"""
    today = date.today()
    try:
        hijri = Gregorian(today.year, today.month, today.day).to_hijri()
        if hijri.month != 9:  # Ramazon = 9-oy
            return None

        day = hijri.day

        # Ramazon oxirini hisoblash: keyingi oy (Shavvol) boshlanguncha
        if day <= 29:
            next_month_hijri = Hijri(hijri.year, 10, 1)  # Shavvol 1
            next_month_gregorian = next_month_hijri.to_gregorian()
            end_date = date(next_month_gregorian.year, next_month_gregorian.month, next_month_gregorian.day)
            left = (end_date - today).days
        else:
            left = 0
            end_date = today

        return day, left, end_date.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Ramazon progressini hisoblashda xato: {e}")
        return None


def get_next_prayer(timings):
    """Keyingi namoz vaqtini va uning nomini aniqlaydi"""
    now = get_local_time()
    prayers = [
        ('Fajr', timings['Fajr']),
        ('Dhuhr', timings['Dhuhr']),
        ('Asr', timings['Asr']),
        ('Maghrib', timings['Maghrib']),
        ('Isha', timings['Isha'])
    ]

    for prayer, t in prayers:
        try:
            h, m = map(int, t.split(':'))
            p_time = time(h, m)
            if p_time > now:
                return prayer, t
        except (ValueError, AttributeError) as e:
            logger.error(f"Namoz vaqtini parse qilishda xato: {prayer}, {t}, {e}")
            continue

    # Agar hammasi o'tgan bo'lsa, ertangi Bomdod
    return 'Fajr', timings['Fajr']


def calculate_remaining_time(target_time_str):
    """Berilgan vaqtgacha qolgan vaqtni odam tushunadigan formatda qaytaradi"""
    try:
        diff = get_remaining_timedelta(target_time_str)
        total_seconds = int(diff.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        return f"{hours} soat {minutes} daqiqa"
    except Exception as e:
        logger.error(f"Qolgan vaqtni hisoblashda xato: {e}")
        return "Noma'lum"


def generate_dua_image(text, lang='uz'):
    """Duo uchun rasm yaratadi"""
    # Ro'za ochish duosi tekshiruvi
    fasting_end_dua_uz = "Allohumma laka sumtu va bika amantu va 'ala rizqika aftartu va 'alayka tavakkaltu, fag'firli ma qoddamtu va ma axxortu. Birrohmannar rohim."

    if text.strip() == fasting_end_dua_uz and lang == 'uz':
        # Ro'za ochish duosi uchun Google Drive rasmini ishlatish
        image_url = "https://share.google.com/images/YSPhn4dCk989PAA4T"
        try:
            response = requests.get(image_url, timeout=15, stream=True)
            response.raise_for_status()

            # Content type tekshiruvi
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type.lower():
                logger.warning(f"URL rasm emas: {content_type}")
                raise ValueError("URL rasm emas")

            image = Image.open(BytesIO(response.content))

            # Instagram story o'lchamiga o'zgartirish
            if image.size != (1080, 1920):
                image = image.resize((1080, 1920), Image.Resampling.LANCZOS)

            # Rasmni saqlash
            image_path = f"dua_{lang}_iftar_{abs(hash(text))}.png"
            image.save(image_path, "PNG")
            return image_path

        except Exception as e:
            logger.error(f"Rasmni yuklashda xato: {e}")
            # Xato bo'lsa, matn asosida rasm yaratish
            return _generate_text_based_dua_image(text, lang, "RO'ZA DUOSI")
    else:
        # Boshqa barcha holatlar uchun matn asosida rasm yaratish
        return _generate_text_based_dua_image(text, lang, "RO'ZA DUOSI")


def _generate_text_based_dua_image(text, lang, title_text):
    """Matn asosida duo rasmi yaratadi"""
    width, height = 1080, 1920
    image = Image.new('RGB', (width, height), color=(0, 30, 0))  # To'q yashil
    draw = ImageDraw.Draw(image)

    # Font yuklash
    font_path = None
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/System/Library/Fonts/Helvetica.ttc",
                 "C:\\Windows\\Fonts\\arial.ttf"]:
        if os.path.exists(path):
            font_path = path
            break

    try:
        if font_path:
            title_font = ImageFont.truetype(font_path, 180)
            text_font = ImageFont.truetype(font_path, 170)
        else:
            raise IOError("Font topilmadi")
    except Exception as e:
        logger.warning(f"Fontni yuklashda xato: {e}, default font ishlatiladi")
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # Dekorativ chegara
    border = 20
    draw.rectangle([border, border, width-border, height-border],
                   outline=(255, 180, 0), width=10)

    # Sarlavha
    title = title_text if lang == 'uz' else "DUA FOR FASTING"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
    title_y = 80

    # Soya effekti
    for offset in [3, 2, 1]:
        draw.text((title_x+offset, title_y+offset), title,
                  fill=(0, 20, 0), font=title_font)

    # Asosiy sarlavha
    draw.text((title_x, title_y), title,
              fill=(255, 255, 180),
              font=title_font,
              stroke_width=5,
              stroke_fill=(0, 80, 0))

    # Matnni qatorlarga bo'lish (har qatorda 2 so'z)
    words = text.split()
    lines = [' '.join(words[i:i+2]) for i in range(0, len(words), 2)]

    # Matnni chizish
    start_y = 300
    line_height = 210

    for i, line in enumerate(lines):
        temp_font_size = 200
        temp_font = text_font

        # Optimal font o'lchamini topish
        while temp_font_size > 60:
            try:
                if font_path:
                    temp_font = ImageFont.truetype(font_path, temp_font_size)
                else:
                    temp_font = ImageFont.load_default()
                    break

                bbox = draw.textbbox((0, 0), line, font=temp_font)
                text_width = bbox[2] - bbox[0]
                if text_width < (width - 120):
                    break
            except Exception:
                pass
            temp_font_size -= 5

        bbox = draw.textbbox((0, 0), line, font=temp_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = start_y + (i * line_height)

        # Soya
        for offset in [3, 2]:
            draw.text((x+offset, y+offset), line,
                      fill=(0, 30, 0), font=temp_font)

        # Asosiy matn
        draw.text((x, y), line,
                  fill=(255, 255, 220),
                  font=temp_font,
                  stroke_width=4,
                  stroke_fill=(0, 80, 0))

    # Rasmni saqlash
    image_path = f"dua_{lang}_{abs(hash(text))}.png"
    image.save(image_path)
    return image_path


def generate_next_prayer_image(title, prayer_name, time_str, remaining_str, lang='uz'):
    """Keyingi namoz uchun rasm yaratadi"""
    prayer_name = strip_emojis(prayer_name)

    # Ka'ba rasmini yuklab olishga harakat
    try:
        kaaba_url = "https://media.gettyimages.com/id/1452831298/de/foto/pilgrims-touching-kiswah-cloth-and-gold-door-of-khana-kaba-people-doing-tawaaf-and-touch.jpg?s=612x612&w=0&k=20&c=E46uzLhOxyVrQdNpftY4Bx5F3pcaIcxLYpGh5-v02EE="
        response = requests.get(kaaba_url, timeout=10)
        response.raise_for_status()
        kaaba_image = Image.open(BytesIO(response.content))
        image = kaaba_image.resize((600, 400), Image.Resampling.LANCZOS)
        # Qoraytirilgan
        image = image.point(lambda p: int(p * 0.5))
    except Exception as e:
        logger.warning(f"Ka'ba rasmini yuklashda xato: {e}, gradient ishlatiladi")
        # Gradient yaratish
        width, height = 600, 400
        color1 = (0, 100, 0)  # To'q yashil
        color2 = (255, 215, 0)  # Oltin
        image = Image.new('RGB', (width, height))
        for y in range(height):
            r = color1[0] + (color2[0] - color1[0]) * y // height
            g = color1[1] + (color2[1] - color1[1]) * y // height
            b = color1[2] + (color2[2] - color1[2]) * y // height
            for x in range(width):
                image.putpixel((x, y), (r, g, b))

    draw = ImageDraw.Draw(image)

    # Font yuklash
    font_path = None
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/System/Library/Fonts/Helvetica.ttc",
                 "C:\\Windows\\Fonts\\arial.ttf"]:
        if os.path.exists(path):
            font_path = path
            break

    try:
        if font_path:
            font = ImageFont.truetype(font_path, 36)
            small_font = ImageFont.truetype(font_path, 28)
        else:
            raise IOError("Font topilmadi")
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Sarlavha
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    x = (600 - text_width) / 2
    draw.text((x, 20), title, fill=(255, 255, 255), font=font)

    # Namoz nomi
    bbox = draw.textbbox((0, 0), prayer_name, font=font)
    text_width = bbox[2] - bbox[0]
    x = (600 - text_width) / 2
    draw.text((x, 100), prayer_name, fill=(255, 215, 0), font=font)

    # Vaqt
    time_labels = {
        'uz': f"Vaqt: {time_str}",
        'en': f"Time: {time_str}",
        'ru': f"Время: {time_str}",
        'ar': f"الوقت: {time_str}",
        'fa': f"زمان: {time_str}"
    }
    time_label = time_labels.get(lang, time_labels['uz'])

    bbox = draw.textbbox((0, 0), time_label, font=small_font)
    text_width = bbox[2] - bbox[0]
    x = (600 - text_width) / 2
    draw.text((x, 200), time_label, fill=(255, 255, 255), font=small_font)

    # Qolgan vaqt
    remaining_labels = {
        'uz': f"Qolgan: {remaining_str}",
        'en': f"Remaining: {remaining_str}",
        'ru': f"Осталось: {remaining_str}",
        'ar': f"المتبقي: {remaining_str}",
        'fa': f"باقی مانده: {remaining_str}"
    }
    remaining_label = remaining_labels.get(lang, remaining_labels['uz'])

    bbox = draw.textbbox((0, 0), remaining_label, font=small_font)
    text_width = bbox[2] - bbox[0]
    x = (600 - text_width) / 2
    draw.text((x, 270), remaining_label, fill=(255, 255, 255), font=small_font)

    # Rasmni saqlash
    image_path = f"prayer_{lang}_{abs(hash((title, prayer_name, time_str, remaining_str)))}.png"
    image.save(image_path)
    return image_path
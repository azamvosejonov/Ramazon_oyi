import requests
from datetime import datetime, date, time
from hijri_converter import Hijri
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

def strip_emojis(text):
    import re
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
    from config import CITIES

    try:
        city_info = CITIES[city_key]
    except KeyError:
        city_info = CITIES['tashkent']  # Fallback to Tashkent

    city = city_info.get('api_name', city_info.get('name'))
    country = city_info.get('api_country', city_info.get('country', 'Uzbekistan'))

    if not city or not country:
        raise ValueError(f"City configuration is missing required fields for '{city_key}'")

    url = "http://api.aladhan.com/v1/timingsByCity"
    params = {
        'city': city,
        'country': country,
        'method': 2,
        'school': 1,  # Hanafi (common in Uzbekistan)
        'iso8601': True
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    try:
        timings = data['data']['timings']
    except (KeyError, TypeError):
        raise ValueError(f"Prayer times API returned unexpected data for {city}/{country}: {data}")

    return timings

def is_ramadan():
    from datetime import date
    today = date.today()
    # Ramadan 2024: March 12 - April 9
    ramadan_start = date(2024, 3, 12)
    ramadan_end = date(2024, 4, 9)
    return ramadan_start <= today <= ramadan_end  # Or assume based on date

def get_ramadan_progress():
    today = date.today()
    try:
        hijri = Hijri(today.year, today.month, today.day)
        if hijri.month != 9:
            return None
        day = hijri.day
        # Assume 30 days
        left = 30 - day
        # Approximate end date
        end_date = today.replace(day=today.day + left)
        return day, left, end_date.strftime("%Y-%m-%d")
    except OverflowError:
        return None

def get_next_prayer(timings):
    now = datetime.now().time()
    prayers = [
        ('Fajr', timings['Fajr']),
        ('Dhuhr', timings['Dhuhr']),
        ('Asr', timings['Asr']),
        ('Maghrib', timings['Maghrib']),
        ('Isha', timings['Isha'])
    ]
    for prayer, t in prayers:
        h, m = map(int, t.split(':'))
        p_time = time(h, m)
        if p_time > now:
            return prayer, t
    # If all passed, next Fajr tomorrow
    h, m = map(int, timings['Fajr'].split(':'))
    return 'Fajr', timings['Fajr']

def calculate_remaining_time(target_time_str):
    now = datetime.now()
    h, m = map(int, target_time_str.split(':'))
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target < now:
        target = target.replace(day=now.day + 1)
    diff = target - now
    hours, remainder = divmod(diff.seconds, 3600)
    minutes = remainder // 60
    return f"{hours} soat {minutes} daqiqa"

def generate_dua_image(text, lang='uz'):
    # Check if this is the fasting end Dua in Uzbek
    fasting_end_dua_uz = "Allohumma laka sumtu va bika amantu va 'ala rizqika aftartu va 'alayka tavakkaltu, fag'firli ma qoddamtu va ma axxortu. Birrohmannar rohim."
    
    if text.strip() == fasting_end_dua_uz and lang == 'uz':
        # Use the specified image URL for fasting end Dua in Uzbek
        image_url = "https://share.google.com/images/YSPhn4dCk989PAA4T"
        try:
            # Download the image
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            
            # Resize to standard story size if needed
            if image.size != (1080, 1920):
                image = image.resize((1080, 1920), Image.Resampling.LANCZOS)
                
            # Save the image
            image_path = f"dua_{lang}_iftar_{hash(text)}.png"
            image.save(image_path, "PNG")
            return image_path
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            # Fall back to text-based image if download fails
            return _generate_text_based_dua_image(text, lang, "RO'ZA DUOSI")
    else:
        # For all other cases, use the standard text-based image
        return _generate_text_based_dua_image(text, lang, "RO'ZA DUOSI")

def _generate_text_based_dua_image(text, lang, title_text):
    # Create a large background (Instagram story size)
    width, height = 1080, 1920
    image = Image.new('RGB', (width, height), color=(0, 30, 0))  # Very dark green
    draw = ImageDraw.Draw(image)
    
    # Load font with error handling
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        # Maximum possible font sizes
        title_font = ImageFont.truetype(font_path, 180)  # Extremely large title
        text_font = ImageFont.truetype(font_path, 170)   # Extremely large main text
    except:
        try:
            # Fallback to regular font if bold not available
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            title_font = ImageFont.truetype(font_path, 120)
            text_font = ImageFont.truetype(font_path, 100)
        except:
            # Fallback to default font if specific font not found
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
    
    # Add thick decorative border (thinner to maximize space for text)
    border = 20
    draw.rectangle([border, border, width-border, height-border], outline=(255, 180, 0), width=10)
    
    # Add title with shadow
    title = title_text if lang == 'uz' else "DUA FOR FASTING"
    
    # Draw title with multiple shadows for better visibility
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
    title_y = 80  # Move title higher
    
    # Draw multiple shadows for 3D effect
    for offset in [3, 2, 1]:
        draw.text((title_x+offset, title_y+offset), title, 
                 fill=(0, 20, 0), font=title_font)
    
    # Draw main title
    draw.text((title_x, title_y), title, 
              fill=(255, 255, 180),  # Brighter yellow tint
              font=title_font,
              stroke_width=5,
              stroke_fill=(0, 80, 0))
    
    # Process text to show only 2 words per line for maximum size
    words = text.split()
    lines = []
    
    # Group into 2 words per line
    for i in range(0, len(words), 2):
        line = ' '.join(words[i:i+2])
        lines.append(line)
    
    # Calculate starting Y position (below title)
    start_y = 300  # Start higher
    line_height = 210  # Slightly reduced to fit more lines if needed
    
    # Draw each line of text with shadow
    for i, line in enumerate(lines):
        # Use maximum font size that fits
        temp_font_size = 200  # Start with very large size
        while temp_font_size > 60:  # Don't go below 60px
            try:
                temp_font = ImageFont.truetype(font_path, temp_font_size)
                bbox = draw.textbbox((0, 0), line, font=temp_font)
                text_width = bbox[2] - bbox[0]
                if text_width < (width - 120):  # 60px padding on each side
                    # Calculate position
                    x = (width - text_width) // 2
                    y = start_y + (i * line_height)
                    break
            except:
                pass
            temp_font_size -= 5
        
        if temp_font_size <= 60:  # If no size worked, use default
            temp_font = text_font
            bbox = draw.textbbox((0, 0), line, font=temp_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = start_y + (i * line_height)
        
        # Draw shadows
        for offset in [3, 2]:
            draw.text((x+offset, y+offset), line, 
                     fill=(0, 30, 0), 
                     font=temp_font)
        
        # Draw main text
        draw.text((x, y), line, 
                 fill=(255, 255, 220),  # Slightly off-white for better visibility
                 font=temp_font,
                 stroke_width=4,
                 stroke_fill=(0, 80, 0))
    
    # Save image
    image_path = f"dua_{lang}_{hash(text)}.png"
    image.save(image_path)
    return image_path

def generate_next_prayer_image(title, prayer_name, time_str, remaining_str, lang='uz'):
    prayer_name = strip_emojis(prayer_name)
    # Try to use Kaaba as background
    try:
        kaaba_url = "https://media.gettyimages.com/id/1452831298/de/foto/pilgrims-touching-kiswah-cloth-and-gold-door-of-khana-kaba-people-doing-tawaaf-and-touch.jpg?s=612x612&w=0&k=20&c=E46uzLhOxyVrQdNpftY4Bx5F3pcaIcxLYpGh5-v02EE="
        response = requests.get(kaaba_url, timeout=10)
        kaaba_image = Image.open(BytesIO(response.content))
        image = kaaba_image.resize((600, 400))
        # Make darker
        image = image.point(lambda p: p * 0.5)
    except:
        # Fallback to gradient
        width, height = 600, 400
        color1 = (0, 100, 0)  # Dark green
        color2 = (255, 215, 0)  # Gold
        image = Image.new('RGB', (width, height))
        for y in range(height):
            r = color1[0] + (color2[0] - color1[0]) * y // height
            g = color1[1] + (color2[1] - color1[1]) * y // height
            b = color1[2] + (color2[2] - color1[2]) * y // height
            for x in range(width):
                image.putpixel((x, y), (r, g, b))
    
    draw = ImageDraw.Draw(image)
    
    # Try to load font
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font = ImageFont.truetype(font_path, 800)
        small_font = ImageFont.truetype(font_path, 700)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Title
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    x = (600 - text_width) / 2
    draw.text((x, 20), title, fill=(255, 255, 255), font=font)
    
    # Prayer name
    bbox = draw.textbbox((0, 0), prayer_name, font=font)
    text_width = bbox[2] - bbox[0]
    x = (600 - text_width) / 2
    draw.text((x, 100), prayer_name, fill=(255, 215, 0), font=font)
    
    # Time
    time_label = f"Vaqt: {time_str}" if lang == 'uz' else f"Time: {time_str}" if lang == 'en' else f"Время: {time_str}" if lang == 'ru' else f"الوقت: {time_str}" if lang == 'ar' else f"زمان: {time_str}"
    bbox = draw.textbbox((0, 0), time_label, font=small_font)
    text_width = bbox[2] - bbox[0]
    x = (600 - text_width) / 2
    draw.text((x, 200), time_label, fill=(255, 255, 255), font=small_font)
    
    # Remaining
    remaining_label = f"Qolgan: {remaining_str}" if lang == 'uz' else f"Remaining: {remaining_str}" if lang == 'en' else f"Осталось: {remaining_str}" if lang == 'ru' else f"المتبقي: {remaining_str}" if lang == 'ar' else f"باقی مانده: {remaining_str}"
    bbox = draw.textbbox((0, 0), remaining_label, font=small_font)
    text_width = bbox[2] - bbox[0]
    x = (600 - text_width) / 2
    draw.text((x, 270), remaining_label, fill=(255, 255, 255), font=small_font)
    
    # Save image
    image_path = f"prayer_{lang}_{hash((title, prayer_name, time_str, remaining_str))}.png"
    image.save(image_path)
    return image_path

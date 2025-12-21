# Python 3.11 slim versiyasidan foydalanish
FROM python:3.11-slim

# Metadata qo'shish
LABEL maintainer="your-email@example.com"
LABEL description="Namoz vaqtlari Telegram bot"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Ish katalogi
WORKDIR /app

# Sistema paketlarini yangilash va kerakli kutubxonalarni o'rnatish
# PIL/Pillow uchun rasm kutubxonalari kerak
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Pillow uchun kerakli kutubxonalar
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    libwebp-dev \
    # Fontlar uchun
    fonts-dejavu-core \
    fonts-dejavu-extra \
    # Vaqt zonasi uchun
    tzdata \
    # Tozalash
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Vaqt zonasini sozlash (Toshkent)
ENV TZ=Asia/Tashkent
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Requirements faylini nusxalash va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Non-root foydalanuvchi yaratish (xavfsizlik uchun)
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Ilovani nusxalash
COPY --chown=botuser:botuser . .

# Data fayllarini yaratish va ruxsatlarni o'rnatish
RUN mkdir -p /app/data && \
    touch /app/data/user_data.json && \
    echo '{}' > /app/data/user_data.json && \
    chown -R botuser:botuser /app/data

# Volume yaratish (ma'lumotlar saqlanishi uchun)
VOLUME ["/app/data"]

# Non-root foydalanuvchiga o'tish
USER botuser

# Health check qo'shish (ixtiyoriy)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/data/user_data.json') else 1)"

# Botni ishga tushirish
CMD ["python", "-u", "main.py"]
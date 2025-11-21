FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force rebuild
COPY . .

# Create user_data.json if not exists
RUN touch user_data.json

CMD ["python", "main.py"]

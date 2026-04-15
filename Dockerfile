FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium and all system dependencies for Playwright
RUN python -m playwright install --with-deps chromium

COPY bot/ ./bot/

CMD ["python", "-m", "bot.main"]

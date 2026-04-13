FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for aiohttp
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove gcc after pip install (no longer needed)
RUN apt-get purge -y gcc && apt-get autoremove -y

COPY bot/ ./bot/

CMD ["python", "-m", "bot.main"]

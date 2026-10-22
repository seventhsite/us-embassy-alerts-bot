# Newest Python minor that all pinned dependencies support. Patch releases
# arrive automatically (base is pulled on every build, see compose); update.sh
# reports when a newer minor becomes installable so this line can be bumped.
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ ./bot/

CMD ["python", "-m", "bot.main"]

FROM python:3.12-slim

RUN python -m pip install --upgrade pip
#RUN apt-get update && apt-get install -y --no-install-recommends \
##    gcc \
#    python3-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY . /app/bot

WORKDIR /app

CMD ["python", "-m", "bot.main"]
FdockeROM python:3.12-slim

RUN python -m pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY . /app/bot

WORKDIR /app

CMD ["python", "-m", "bot.main"]

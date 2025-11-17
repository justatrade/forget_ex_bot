FROM python:3.12-slim

RUN python -m pip install --upgrade pip
RUN pip install pydevd-pycharm~=243.0


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY . /app/bot

WORKDIR /app

CMD ["python", "-m", "bot.main"]

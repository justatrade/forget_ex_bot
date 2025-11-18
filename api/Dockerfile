FROM python:3.12-slim

RUN python -m pip install --upgrade pip
RUN pip install pydevd-pycharm~=243.0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY bot /apo/bot
COPY . /app/api

WORKDIR /app

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
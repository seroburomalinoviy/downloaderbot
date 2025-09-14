# Используем официальный Python 3.12 slim
FROM python:3.12-slim

# --- Установка системных зависимостей ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git && \
    rm -rf /var/lib/apt/lists/*

# --- Создание рабочей директории ---
WORKDIR /app

# --- Копирование скрипта бота ---
COPY bot_polling.py /app/
COPY requests.txt /app/

# --- Установка Python-пакетов ---
RUN pip install --no-cache-dir -r requests.txt

# --- Точка входа ---
CMD ["python", "bot_polling.py"]

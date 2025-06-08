# Используем официальный образ Python
FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libmagic1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание необходимых директорий и установка прав
RUN mkdir -p uploads backups logs search_index && \
    chmod 777 uploads backups logs search_index && \
    touch /app/logs/imageboard.log && \
    chmod 666 /app/logs/imageboard.log

# Переключение на непривилегированного пользователя
USER nobody

# Открытие порта
EXPOSE 5000

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"] 
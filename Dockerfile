# Используем официальный образ Python
FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    libmagickwand-dev \
    imagemagick \
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

# Создание необходимых директорий
RUN mkdir -p uploads backups logs search_index

# Установка прав доступа
RUN chmod 755 uploads backups logs search_index

# Открытие порта
EXPOSE 5000

# Запуск приложения
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"] 
# Используем официальный образ Python
FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libmagic1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Создание необходимых директорий и файлов
RUN mkdir -p uploads backups logs search_index && \
    touch /app/logs/imageboard.log && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod 777 uploads backups logs search_index && \
    chmod 666 /app/logs/imageboard.log

# Копирование исходного кода
COPY --chown=appuser:appuser . .

# Переключение на непривилегированного пользователя
USER appuser

# Открытие порта
EXPOSE 5000

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "120", "--keep-alive", "5", "--log-level", "info", "app:app"]
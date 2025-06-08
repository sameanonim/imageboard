#!/bin/bash

# Обновление списка пакетов
echo "Обновление списка пакетов..."
sudo apt-get update

# Установка Git
echo "Установка Git..."
sudo apt-get install -y git

# Клонирование репозитория
echo "Клонирование репозитория..."
if [ ! -d "imageboard" ]; then
    git clone https://github.com/your-username/imageboard.git
    cd imageboard
else
    cd imageboard
    git pull
fi

# Установка Python и pip
echo "Установка Python и pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Установка PostgreSQL
echo "Установка PostgreSQL..."
sudo apt-get install -y postgresql postgresql-contrib

# Установка Redis
echo "Установка Redis..."
sudo apt-get install -y redis-server

# Установка системных зависимостей для работы с изображениями
echo "Установка системных зависимостей для работы с изображениями..."
sudo apt-get install -y libmagickwand-dev imagemagick

# Установка системных зависимостей для работы с видео
echo "Установка системных зависимостей для работы с видео..."
sudo apt-get install -y ffmpeg

# Создание и активация виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Установка Python-зависимостей
echo "Установка Python-зависимостей..."
pip install --upgrade pip
pip install flask
pip install flask-sqlalchemy
pip install flask-login
pip install flask-wtf
pip install flask-migrate
pip install flask-babel
pip install flask-socketio
pip install celery
pip install redis
pip install python-dotenv
pip install pillow
pip install python-magic
pip install gunicorn
pip install pytest
pip install coverage
pip install psycopg2-binary  # Драйвер PostgreSQL

# Настройка PostgreSQL
echo "Настройка PostgreSQL..."
sudo -u postgres psql -c "CREATE USER imageboard WITH PASSWORD 'imageboard';"
sudo -u postgres psql -c "CREATE DATABASE imageboard OWNER imageboard;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE imageboard TO imageboard;"

# Консольная настройка борды
echo "\n--- Настройка Imageboard ---"

# FLASK_ENV и DEBUG
read -p "Выберите среду выполнения (development/production) [development]: " FLASK_ENV
FLASK_ENV=${FLASK_ENV:-development}

DEBUG_DEFAULT="True"
if [ "$FLASK_ENV" == "production" ]; then
    DEBUG_DEFAULT="False"
fi
read -p "Включить режим отладки (True/False) [${DEBUG_DEFAULT}]: " FLASK_DEBUG
FLASK_DEBUG=${FLASK_DEBUG:-${DEBUG_DEFAULT}}

# DATABASE_URL
read -p "Введите URL базы данных (например, postgresql://user:pass@host/db) [postgresql://imageboard:imageboard@localhost/imageboard]: " DATABASE_URL
DATABASE_URL=${DATABASE_URL:-postgresql://imageboard:imageboard@localhost/imageboard}

# REDIS_URL
read -p "Введите URL Redis (например, redis://localhost:6379/0) [redis://localhost:6379/0]: " REDIS_URL
REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}

# UPLOAD_FOLDER
read -p "Введите папку для загрузки файлов [uploads]: " UPLOAD_FOLDER
UPLOAD_FOLDER=${UPLOAD_FOLDER:-uploads}

# MAX_CONTENT_LENGTH
read -p "Введите максимальный размер загружаемого файла в МБ (например, 16 для 16МБ) [16]: " MAX_CONTENT_LENGTH_MB
MAX_CONTENT_LENGTH_MB=${MAX_CONTENT_LENGTH_MB:-16}
MAX_CONTENT_LENGTH=$((MAX_CONTENT_LENGTH_MB * 1024 * 1024))

# ALLOWED_EXTENSIONS
read -p "Введите разрешенные расширения файлов через запятую (например, png,jpg,jpeg,gif,webp,mp4,webm) [png,jpg,jpeg,gif,webp,mp4,webm]: " ALLOWED_EXTENSIONS_STR
ALLOWED_EXTENSIONS_STR=${ALLOWED_EXTENSIONS_STR:-png,jpg,jpeg,gif,webp,mp4,webm}

# MAX_FILES_PER_POST
read -p "Введите максимальное количество файлов на один пост [4]: " MAX_FILES_PER_POST
MAX_FILES_PER_POST=${MAX_FILES_PER_POST:-4}

# LOG_LEVEL
read -p "Введите уровень логирования (INFO/DEBUG/WARNING/ERROR) [INFO]: " LOG_LEVEL
LOG_LEVEL=${LOG_LEVEL:-INFO}

# DEFAULT_LANGUAGE
read -p "Введите язык по умолчанию (ru/en) [ru]: " DEFAULT_LANGUAGE
DEFAULT_LANGUAGE=${DEFAULT_LANGUAGE:-ru}

# THEME_DEFAULT
read -p "Введите тему по умолчанию (light/dark) [light]: " THEME_DEFAULT
THEME_DEFAULT=${THEME_DEFAULT:-light}

# SECRET_KEY - генерируется автоматически
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
PASSWORD_SALT=$(python3 -c 'import secrets; print(secrets.token_hex(16))')

# Создание необходимых директорий
echo "Создание необходимых директорий..."
mkdir -p "${UPLOAD_FOLDER}"
mkdir -p backups
mkdir -p logs
mkdir -p search_index

# Установка прав доступа
echo "Установка прав доступа..."
chmod 755 "${UPLOAD_FOLDER}"
chmod 755 backups
chmod 755 logs
chmod 755 search_index

# Создание файла .env
echo "Создание файла .env..."
cat > .env << EOL
FLASK_APP=app.py
FLASK_ENV=${FLASK_ENV}
FLASK_DEBUG=${FLASK_DEBUG}
DATABASE_URL=${DATABASE_URL}
SECRET_KEY=${SECRET_KEY}
PASSWORD_SALT=${PASSWORD_SALT}
REDIS_URL=${REDIS_URL}
UPLOAD_FOLDER=${UPLOAD_FOLDER}
MAX_CONTENT_LENGTH=${MAX_CONTENT_LENGTH}
ALLOWED_EXTENSIONS=${ALLOWED_EXTENSIONS_STR}
MAX_FILES_PER_POST=${MAX_FILES_PER_POST}
LOG_LEVEL=${LOG_LEVEL}
DEFAULT_LANGUAGE=${DEFAULT_LANGUAGE}
THEME_DEFAULT=${THEME_DEFAULT}
EOL

# Инициализация базы данных
echo "Инициализация базы данных..."
flask db upgrade

# Запуск Celery
echo "Запуск Celery..."
celery -A app.celery worker --loglevel=info --detach

# Запуск Redis
echo "Запуск Redis..."
sudo systemctl start redis

# Запуск приложения
echo "Запуск приложения..."
if [ "$FLASK_ENV" == "production" ]; then
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
else
    flask run
fi 
#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Функция для вывода сообщений
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция для определения дистрибутива Linux
get_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo $ID
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        echo $DISTRIB_ID | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown"
    fi
}

# Функция установки Docker
install_docker() {
    local distro=$(get_distro)
    print_message "Определен дистрибутив: $distro"
    
    case $distro in
        "ubuntu"|"debian")
            print_message "Установка Docker для Ubuntu/Debian..."
            # Удаление старых версий
            sudo apt-get remove docker docker-engine docker.io containerd runc
            
            # Обновление списка пакетов
            sudo apt-get update
            
            # Установка зависимостей
            sudo apt-get install -y \
                apt-transport-https \
                ca-certificates \
                curl \
                gnupg \
                lsb-release
            
            # Добавление GPG ключа Docker
            curl -fsSL https://download.docker.com/linux/$distro/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # Настройка репозитория
            echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$distro \
                $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Установка Docker
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            
            # Добавление текущего пользователя в группу docker
            sudo usermod -aG docker $USER
            print_message "Пользователь $USER добавлен в группу docker"
            print_message "Пожалуйста, перезайдите в систему для применения изменений"
            ;;
            
        "fedora")
            print_message "Установка Docker для Fedora..."
            sudo dnf -y install dnf-plugins-core
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            print_message "Пользователь $USER добавлен в группу docker"
            print_message "Пожалуйста, перезайдите в систему для применения изменений"
            ;;
            
        "centos"|"rhel")
            print_message "Установка Docker для CentOS/RHEL..."
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            print_message "Пользователь $USER добавлен в группу docker"
            print_message "Пожалуйста, перезайдите в систему для применения изменений"
            ;;
            
        *)
            print_error "Неподдерживаемый дистрибутив Linux: $distro"
            print_error "Пожалуйста, установите Docker вручную: https://docs.docker.com/engine/install/"
            exit 1
            ;;
    esac
}

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    print_message "Docker не найден. Начинаем установку..."
    install_docker
    print_error "Docker установлен. Пожалуйста, перезайдите в систему и запустите скрипт снова."
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_message "Docker Compose не найден. Устанавливаем..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Проверка статуса Docker
if ! docker info &> /dev/null; then
    print_error "Docker не запущен. Пожалуйста, запустите Docker и перезапустите скрипт."
    exit 1
fi

# Создание рабочей директории
WORK_DIR="imageboard"
if [ ! -d "$WORK_DIR" ]; then
    print_message "Создание рабочей директории..."
    mkdir -p "$WORK_DIR"
fi

# Переход в рабочую директорию
cd "$WORK_DIR"

# Клонирование репозитория
if [ ! -d ".git" ]; then
    print_message "Клонирование репозитория..."
    git clone https://github.com/sameanonim/imageboard.git .
    if [ $? -ne 0 ]; then
        print_error "Ошибка при клонировании репозитория"
        exit 1
    fi
else
    print_message "Обновление репозитория..."
    git pull
    if [ $? -ne 0 ]; then
        print_error "Ошибка при обновлении репозитория"
        exit 1
    fi
fi

# Создание необходимых директорий
print_message "Создание необходимых директорий..."
mkdir -p uploads backups logs search_index celery

# Установка прав доступа
print_message "Установка прав доступа..."
chmod 755 uploads backups logs search_index celery

# Настройка Redis
print_message "Настройка Redis..."
if [ -f /etc/redis/redis.conf ]; then
    # Ubuntu/Debian
    sudo sed -i 's/^# maxmemory .*/maxmemory 512mb/' /etc/redis/redis.conf
    sudo sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    sudo systemctl restart redis
elif [ -f /etc/redis.conf ]; then
    # CentOS/RHEL
    sudo sed -i 's/^# maxmemory .*/maxmemory 512mb/' /etc/redis.conf
    sudo sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis.conf
    sudo systemctl restart redis
fi

# Настройка Celery
print_message "Настройка Celery..."
cat > celery_config.py << EOL
from celery import Celery
from kombu import Queue, Exchange

# Настройки Celery
broker_url = 'redis://redis:6379/0'
result_backend = 'redis://redis:6379/0'

# Настройки очередей
task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('image_processing', Exchange('image_processing'), routing_key='image_processing'),
    Queue('video_processing', Exchange('video_processing'), routing_key='video_processing'),
)

# Настройки маршрутизации
task_routes = {
    'app.tasks.process_image': {'queue': 'image_processing'},
    'app.tasks.process_video': {'queue': 'video_processing'},
}

# Настройки производительности
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000
worker_max_memory_per_child = 200000  # 200MB

# Настройки логирования
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Настройки повторных попыток
task_acks_late = True
task_reject_on_worker_lost = True
task_default_retry_delay = 300  # 5 минут
task_max_retries = 3
EOL

# Создание systemd сервиса для Celery
print_message "Создание systemd сервиса для Celery..."
sudo tee /etc/systemd/system/celery.service << EOL
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/celery -A app.celery worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Перезагрузка systemd и запуск Celery
print_message "Запуск Celery..."
sudo systemctl daemon-reload
sudo systemctl enable celery
sudo systemctl start celery

# Сборка Docker образов
print_message "Сборка Docker образов..."
docker-compose build
if [ $? -ne 0 ]; then
    print_error "Ошибка при сборке Docker образов"
    exit 1
fi

# Запуск контейнеров
print_message "Запуск контейнеров..."
docker-compose up -d
if [ $? -ne 0 ]; then
    print_error "Ошибка при запуске контейнеров"
    exit 1
fi

# Ожидание готовности базы данных
print_message "Ожидание готовности базы данных..."
sleep 10

# Инициализация базы данных
print_message "Инициализация базы данных..."
docker-compose exec web flask db upgrade
if [ $? -ne 0 ]; then
    print_error "Ошибка при инициализации базы данных"
    exit 1
fi

# Проверка статуса Celery
print_message "Проверка статуса Celery..."
if systemctl is-active --quiet celery; then
    print_message "Celery успешно запущен"
else
    print_error "Celery не запущен. Проверьте логи: journalctl -u celery"
fi

print_message "Развертывание завершено успешно!"
print_message "Приложение доступно по адресу: http://localhost:5000"
print_message "Для просмотра логов используйте команды:"
print_message "- Docker: docker-compose logs -f"
print_message "- Celery: journalctl -u celery -f" 

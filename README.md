# Imageboard

Современная имиджборда с поддержкой изображений, видео и WebSocket-уведомлений.

## Особенности

- 🖼️ Поддержка изображений и видео
- 🔔 WebSocket-уведомления в реальном времени
- 🔒 Двухфакторная аутентификация для администраторов
- 🏆 Система достижений
- 📊 Кэширование популярных тредов
- 🔄 Асинхронная обработка файлов
- 🌐 Многоязычный интерфейс
- 📱 Адаптивный дизайн
- 🔍 Поиск по тредам и постам
- 📦 Система резервного копирования

## Требования

- Docker Desktop
- Git
- Bash (для Linux/Mac) или PowerShell (для Windows)

## Быстрое развертывание

### Linux/Mac

1. Скачайте скрипт развертывания:
```bash
curl -O https://raw.githubusercontent.com/sameanonim/imageboard/main/deploy.sh
```

2. Сделайте скрипт исполняемым:
```bash
chmod +x deploy.sh
```

3. Запустите скрипт:
```bash
./deploy.sh
```

### Windows

1. Скачайте скрипт развертывания:
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/sameanonim/imageboard/main/deploy.ps1" -OutFile "deploy.ps1"
```

2. Запустите PowerShell от имени администратора и выполните:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
.\deploy.ps1
```

## Ручное развертывание

1. Клонируйте репозиторий:
```bash
git clone https://github.com/sameanonim/imageboard.git
cd imageboard
```

2. Создайте необходимые директории:

Linux/Mac:
```bash
mkdir -p uploads backups logs search_index
chmod 755 uploads backups logs search_index
```

Windows:
```powershell
New-Item -ItemType Directory -Force -Path uploads, backups, logs, search_index
```

3. Соберите и запустите контейнеры:
```bash
docker-compose build
docker-compose up -d
```

4. Инициализируйте базу данных:
```bash
docker-compose exec web flask db upgrade
```

## Доступ к приложению

После успешного развертывания приложение будет доступно по адресу:
http://localhost:5000

## Управление контейнерами

- Просмотр логов:
```bash
docker-compose logs -f
```

- Остановка контейнеров:
```bash
docker-compose down
```

- Перезапуск контейнеров:
```bash
docker-compose restart
```

## Структура проекта

- `web` - основной контейнер с приложением
- `db` - контейнер с PostgreSQL
- `redis` - контейнер с Redis
- `celery` - контейнер с Celery worker

## Переменные окружения

Основные настройки приложения находятся в файле `.env`. При первом запуске он будет создан автоматически.

## Обновление

Для обновления приложения до последней версии:

```bash
git pull
docker-compose build
docker-compose up -d
docker-compose exec web flask db upgrade
```

## Запуск

1. Запустите Redis:
```bash
redis-server
```

2. Запустите Celery worker:
```bash
celery -A celery_worker.celery worker --loglevel=info
```

3. Запустите приложение:
```bash
flask run
```

## Структура проекта

```
imageboard/
├── app.py                 # Основной файл приложения
├── config.py             # Конфигурация
├── requirements.txt      # Зависимости
├── celery_worker.py      # Celery worker
├── cli.py               # CLI команды
├── models/              # Модели базы данных
├── static/              # Статические файлы
│   ├── css/            # Стили
│   ├── js/             # JavaScript
│   └── uploads/        # Загруженные файлы
├── templates/           # Шаблоны
├── translations/        # Переводы
└── utils/              # Утилиты
    ├── achievements.py # Система достижений
    ├── backup.py      # Резервное копирование
    ├── cache.py       # Кэширование
    ├── socket.py      # WebSocket
    └── tasks.py       # Асинхронные задачи
```

## Использование

### Администраторы

1. Вход в админ-панель:
   - Перейдите на страницу входа
   - Войдите с учетными данными администратора
   - Нажмите "Админка" в меню

2. Управление тредами:
   - Блокировка/разблокировка тредов
   - Удаление постов
   - Модерация контента

3. Резервное копирование:
   - Создание резервных копий
   - Восстановление из резервной копии
   - Управление резервными копиями

### Пользователи

1. Создание треда:
   - Нажмите "Новый тред"
   - Заполните форму
   - Загрузите изображение или видео
   - Нажмите "Создать"

2. Ответ в треде:
   - Откройте тред
   - Заполните форму ответа
   - Загрузите файл (опционально)
   - Нажмите "Отправить"

3. Достижения:
   - Создавайте треды
   - Отвечайте в тредах
   - Загружайте файлы
   - Получайте достижения

## Безопасность

- Двухфакторная аутентификация для администраторов
- Защита от CSRF и XSS
- Ограничение частоты запросов
- Безопасная обработка файлов
- Резервное копирование данных

## Оптимизация

- Кэширование популярных тредов
- Асинхронная обработка файлов
- Оптимизация изображений
- Сжатие статических файлов
- Минимизация JavaScript

## Разработка

1. Установите зависимости для разработки:
```bash
pip install -r requirements-dev.txt
```

2. Запустите тесты:
```bash
pytest
```

3. Проверьте код:
```bash
flake8
mypy .
```

## Лицензия

MIT License. См. файл LICENSE для подробностей.

## Устранение неполадок

### Windows

1. Если возникает ошибка с правами выполнения скрипта:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
```

2. Если Docker не запускается:
- Убедитесь, что Docker Desktop запущен
- Проверьте, что WSL2 установлен и включен
- Перезапустите Docker Desktop

### Linux

1. Если возникают проблемы с правами доступа:
```bash
sudo chown -R $USER:$USER .
```

2. Если порт 5000 занят:
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
``` 
# Цвета для вывода
$Green = [System.ConsoleColor]::Green
$Red = [System.ConsoleColor]::Red

# Функция для вывода сообщений
function Write-Message {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Green
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

# Проверка наличия Docker
try {
    $dockerVersion = docker --version
    Write-Message "Docker найден: $dockerVersion"
} catch {
    Write-Error "Docker не установлен. Пожалуйста, установите Docker Desktop."
    exit 1
}

# Проверка наличия Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Message "Docker Compose найден: $composeVersion"
} catch {
    Write-Error "Docker Compose не установлен. Пожалуйста, установите Docker Desktop."
    exit 1
}

# Проверка статуса Docker
try {
    $dockerInfo = docker info
    Write-Message "Docker запущен и готов к работе"
} catch {
    Write-Error "Docker не запущен. Пожалуйста, запустите Docker Desktop."
    exit 1
}

# Создание рабочей директории
$WORK_DIR = "imageboard"
if (-not (Test-Path $WORK_DIR)) {
    Write-Message "Создание рабочей директории..."
    New-Item -ItemType Directory -Path $WORK_DIR | Out-Null
}

# Переход в рабочую директорию
Set-Location $WORK_DIR

# Клонирование репозитория
if (-not (Test-Path ".git")) {
    Write-Message "Клонирование репозитория..."
    git clone https://github.com/sameanonim/imageboard.git .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Ошибка при клонировании репозитория"
        exit 1
    }
} else {
    Write-Message "Обновление репозитория..."
    git pull
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Ошибка при обновлении репозитория"
        exit 1
    }
}

# Создание необходимых директорий
Write-Message "Создание необходимых директорий..."
$directories = @("uploads", "backups", "logs", "search_index")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}

# Сборка Docker образов
Write-Message "Сборка Docker образов..."
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ошибка при сборке Docker образов"
    exit 1
}

# Запуск контейнеров
Write-Message "Запуск контейнеров..."
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ошибка при запуске контейнеров"
    exit 1
}

# Ожидание готовности базы данных
Write-Message "Ожидание готовности базы данных..."
Start-Sleep -Seconds 10

# Инициализация базы данных
Write-Message "Инициализация базы данных..."
docker-compose exec web flask db upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ошибка при инициализации базы данных"
    exit 1
}

Write-Message "Развертывание завершено успешно!"
Write-Message "Приложение доступно по адресу: http://localhost:5000"
Write-Message "Для просмотра логов используйте команду: docker-compose logs -f" 
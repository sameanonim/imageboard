from typing import Dict, Any
from celery import Celery
from kombu import Queue, Exchange
from config import Config
import os

# Константы
REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DB = 0
DEFAULT_RETRY_DELAY = 300  # 5 минут
MAX_RETRIES = 3
MAX_MEMORY_PER_CHILD = 200000  # 200MB
MAX_TASKS_PER_CHILD = 1000

# Настройки подключения
BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')

# Настройки очередей
task_queues = (
    Queue('celery', routing_key='celery'),
    Queue('image_processing', routing_key='image_processing'),
    Queue('video_processing', routing_key='video_processing'),
)

# Настройки маршрутизации
task_routes = {
    'utils.tasks.process_image': {'queue': 'image_processing'},
    'utils.tasks.process_video': {'queue': 'video_processing'},
}

# Настройки производительности
WORKER_PREFETCH_MULTIPLIER = 1
WORKER_MAX_TASKS_PER_CHILD = MAX_TASKS_PER_CHILD
WORKER_MAX_MEMORY_PER_CHILD = MAX_MEMORY_PER_CHILD
WORKER_CONCURRENCY = 2

# Настройки логирования
WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Настройки повторных попыток
TASK_ACKS_LATE = True
TASK_REJECT_ON_WORKER_LOST = True
TASK_DEFAULT_RETRY_DELAY = DEFAULT_RETRY_DELAY
TASK_MAX_RETRIES = MAX_RETRIES

# Настройки брокера
broker_url = 'amqp://guest:guest@rabbitmq:5672//'
result_backend = 'redis://redis:6379/0'

# Настройки безопасности
worker_user = 'celery'
worker_group = 'celery'

def make_celery(app: Any) -> Celery:
    """
    Создает и настраивает экземпляр Celery для приложения.
    
    Args:
        app: Flask приложение
        
    Returns:
        Celery: Настроенный экземпляр Celery
    """
    celery = Celery(
        app.import_name,
        broker=BROKER_URL,
        backend=RESULT_BACKEND
    )
    
    # Обновляем конфигурацию из приложения
    celery.conf.update(app.config)
    
    # Добавляем контекст приложения к задачам
    class ContextTask(celery.Task):
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
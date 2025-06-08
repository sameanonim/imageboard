import os
import logging
from app import create_app, celery
from celery.signals import worker_ready, worker_shutdown, task_failure
from celery.exceptions import MaxRetriesExceededError

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем приложение
app = create_app()
app.app_context().push()

@worker_ready.connect
def worker_ready_handler(sender, **kwargs):
    """Обработчик события готовности воркера."""
    logger.info(f"Воркер {sender.hostname} готов к работе")

@worker_shutdown.connect
def worker_shutdown_handler(sender, **kwargs):
    """Обработчик события завершения работы воркера."""
    logger.info(f"Воркер {sender.hostname} завершает работу")

@task_failure.connect
def task_failure_handler(sender, task_id, exception, args, kwargs, traceback, einfo, **kw):
    """Обработчик ошибок задач."""
    logger.error(
        f"Ошибка в задаче {sender.name} (ID: {task_id}): {str(exception)}\n"
        f"Аргументы: {args}\n"
        f"Параметры: {kwargs}\n"
        f"Трассировка: {traceback}"
    )

if __name__ == '__main__':
    # Настройка окружения
    environment = os.getenv('FLASK_ENV', 'development')
    logger.info(f"Запуск Celery воркера в окружении: {environment}")
    
    # Запуск воркера
    celery.worker_main(['worker', '--loglevel=INFO']) 
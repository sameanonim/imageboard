from celery import Celery
from kombu import Queue, Exchange
from config import Config

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

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=broker_url,
        backend=result_backend
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
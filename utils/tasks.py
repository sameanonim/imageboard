from celery import Celery
from celery.signals import task_failure
from PIL import Image
import os
import logging
import subprocess
from datetime import datetime
from models import db, File
from config import Config


logger = logging.getLogger(__name__)
celery = Celery('imageboard')


def init_celery(app):
    """Инициализация Celery."""
    try:
        celery.conf.update(
            broker_url=app.config['CELERY_BROKER_URL'],
            result_backend=app.config['CELERY_RESULT_BACKEND'],
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=3600,
            task_soft_time_limit=3000,
            worker_max_tasks_per_child=1000,
            worker_prefetch_multiplier=1
        )
        logger.info('Celery initialized successfully')
    except Exception as e:
        logger.error(f'Error initializing Celery: {str(e)}')
        raise


@task_failure.connect
def handle_task_failure(task_id, exception, args, kwargs, traceback, einfo, **kw):
    """Обработка ошибок задач."""
    logger.error(f'Task {task_id} failed: {str(exception)}')


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_image(self, file_path, file_id):
    """Обработка изображения."""
    try:
        file = File.query.get(file_id)
        if not file:
            raise ValueError(f'File {file_id} not found')

        # Проверка формата
        if not file.is_image:
            raise ValueError('File is not an image')

        # Открытие изображения
        with Image.open(file_path) as img:
            # Проверка размера
            if img.size[0] > Config.MAX_IMAGE_SIZE or img.size[1] > Config.MAX_IMAGE_SIZE:
                # Изменение размера
                img.thumbnail((Config.MAX_IMAGE_SIZE, Config.MAX_IMAGE_SIZE))
                img.save(file_path, quality=85, optimize=True)
                logger.info(f'Image {file_id} resized')

            # Создание превью
            thumb_path = os.path.join(
                os.path.dirname(file_path),
                f'thumb_{os.path.basename(file_path)}'
            )
            img.thumbnail((200, 200))
            img.save(thumb_path, quality=85, optimize=True)
            logger.info(f'Thumbnail created for {file_id}')

            # Обновление информации о файле
            file.processed = True
            file.thumbnail_path = thumb_path
            file.error = None
            db.session.commit()
            logger.info(f'Image {file_id} processed successfully')

    except Exception as e:
        logger.error(f'Error processing image {file_id}: {str(e)}')
        if file:
            file.error = str(e)
            db.session.commit()
        self.retry(exc=e)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_video(self, file_path, file_id):
    """Обработка видео."""
    try:
        file = File.query.get(file_id)
        if not file:
            raise ValueError(f'File {file_id} not found')

        # Проверка формата
        if not file.is_video:
            raise ValueError('File is not a video')

        # Создание превью
        thumb_path = os.path.join(
            os.path.dirname(file_path),
            f'thumb_{os.path.basename(file_path)}.jpg'
        )
        cmd = [
            'ffmpeg', '-i', file_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-y', thumb_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f'Thumbnail created for video {file_id}')

        # Обновление информации о файле
        file.processed = True
        file.thumbnail_path = thumb_path
        file.error = None
        db.session.commit()
        logger.info(f'Video {file_id} processed successfully')

    except Exception as e:
        logger.error(f'Error processing video {file_id}: {str(e)}')
        if file:
            file.error = str(e)
            db.session.commit()
        self.retry(exc=e)


@celery.task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_unused_files(self):
    """Очистка неиспользуемых файлов."""
    try:
        # Получение всех файлов без связанных постов
        unused_files = File.query.filter(~File.posts.any()).all()
        
        for file in unused_files:
            try:
                # Удаление файла
                if os.path.exists(file.path):
                    os.remove(file.path)
                    logger.info(f'File {file.id} removed')

                # Удаление превью
                if file.thumbnail_path and os.path.exists(file.thumbnail_path):
                    os.remove(file.thumbnail_path)
                    logger.info(f'Thumbnail for file {file.id} removed')

                # Удаление записи из БД
                db.session.delete(file)
                logger.info(f'File {file.id} deleted from database')

            except Exception as e:
                logger.error(f'Error cleaning up file {file.id}: {str(e)}')
                continue

        db.session.commit()
        logger.info('Cleanup completed successfully')

    except Exception as e:
        logger.error(f'Error during cleanup: {str(e)}')
        self.retry(exc=e)


@celery.task
def update_file_stats():
    """Обновление статистики файлов."""
    try:
        files = File.query.all()
        for file in files:
            try:
                if os.path.exists(file.path):
                    file.size = os.path.getsize(file.path)
                    file.last_modified = datetime.fromtimestamp(
                        os.path.getmtime(file.path)
                    )
                    logger.info(f'Stats updated for file {file.id}')
            except Exception as e:
                logger.error(f'Error updating stats for file {file.id}: {str(e)}')
                continue

        db.session.commit()
        logger.info('File stats updated successfully')

    except Exception as e:
        logger.error(f'Error updating file stats: {str(e)}') 
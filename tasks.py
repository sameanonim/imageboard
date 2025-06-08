from typing import Optional, Any, List, Dict, Union, Tuple
from celery import shared_task, Task
from PIL import Image
import os
from pathlib import Path
from flask import current_app
import magic
import subprocess
import logging
from models import db, File
from celery.exceptions import MaxRetriesExceededError
from functools import wraps
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseTask(Task):
    """Базовый класс для всех задач Celery."""
    
    abstract = True
    
    def on_failure(self, exc: Exception, task_id: str, args: Tuple, kwargs: Dict, einfo: Any) -> None:
        """
        Обработка ошибки выполнения задачи.
        
        Args:
            exc: Исключение
            task_id: ID задачи
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
            einfo: Информация об исключении
        """
        logger.error(f'Task {task_id} failed: {exc}')
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval: Any, task_id: str, args: Tuple, kwargs: Dict) -> None:
        """
        Обработка успешного выполнения задачи.
        
        Args:
            retval: Результат выполнения
            task_id: ID задачи
            args: Аргументы задачи
            kwargs: Именованные аргументы задачи
        """
        logger.info(f'Task {task_id} completed successfully')
        super().on_success(retval, task_id, args, kwargs)

def with_app_context(func: Any) -> Any:
    """
    Декоратор для выполнения функции в контексте приложения.
    
    Args:
        func: Функция для выполнения
        
    Returns:
        Any: Обернутая функция
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with current_app.app_context():
            return func(*args, **kwargs)
    return wrapper

def update_file_status(file_id: int, processed: bool = True, error: Optional[str] = None, 
                      thumbnail_path: Optional[str] = None) -> None:
    """
    Обновление статуса файла в базе данных.
    
    Args:
        file_id: ID файла
        processed: Обработан ли файл
        error: Сообщение об ошибке
        thumbnail_path: Путь к превью
    """
    file = File.query.get(file_id)
    if file:
        file.processed = processed
        if error is not None:
            file.error = error
        if thumbnail_path is not None:
            file.thumbnail_path = thumbnail_path
        file.last_modified = datetime.utcnow()
        db.session.commit()
        logger.info(f"Статус файла {file_id} обновлен: processed={processed}, error={error}")
    else:
        logger.warning(f"Файл {file_id} не найден в базе данных")

@shared_task(bind=True, max_retries=3, default_retry_delay=300, base=BaseTask)
def process_image(self, file_path: str, file_id: int) -> bool:
    """
    Обрабатывает загруженное изображение.
    
    Args:
        file_path: Путь к файлу изображения
        file_id: ID файла в базе данных
        
    Returns:
        bool: True если обработка успешна
        
    Raises:
        ValueError: При неподдерживаемом формате
        Exception: При других ошибках обработки
    """
    start_time = time.time()
    try:
        logger.info(f"Начало обработки изображения {file_path} (ID: {file_id})")
        
        # Открываем изображение
        with Image.open(file_path) as img:
            # Проверяем формат
            if img.format not in current_app.config['ALLOWED_IMAGE_FORMATS']:
                error_msg = f'Неподдерживаемый формат изображения: {img.format}'
                logger.error(error_msg)
                update_file_status(file_id, processed=False, error=error_msg)
                raise ValueError(error_msg)
            
            # Изменяем размер, если нужно
            if img.size[0] > current_app.config['MAX_IMAGE_SIZE'][0] or \
               img.size[1] > current_app.config['MAX_IMAGE_SIZE'][1]:
                logger.info(f"Изменение размера изображения с {img.size} на {current_app.config['MAX_IMAGE_SIZE']}")
                img.thumbnail(current_app.config['MAX_IMAGE_SIZE'])
            
            # Сохраняем обработанное изображение
            img.save(file_path, optimize=True, quality=85)
            
            # Создаем превью
            preview_path = Path(file_path).with_name(f'thumb_{Path(file_path).name}')
            img.thumbnail(current_app.config['THUMBNAIL_SIZE'])
            img.save(preview_path, optimize=True, quality=85)
            
            # Обновляем информацию о файле
            update_file_status(file_id, thumbnail_path=str(preview_path))
            
            processing_time = time.time() - start_time
            logger.info(f"Изображение успешно обработано (ID: {file_id}, время: {processing_time:.2f}с)")
            return True
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения {file_path}: {str(e)}")
        update_file_status(file_id, processed=False, error=str(e))
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(f"Превышено максимальное количество попыток обработки изображения {file_path}")
            raise

@shared_task(bind=True, max_retries=3, default_retry_delay=300, base=BaseTask)
def process_video(self, file_path: str, file_id: int) -> bool:
    """
    Обрабатывает загруженное видео.
    
    Args:
        file_path: Путь к файлу видео
        file_id: ID файла в базе данных
        
    Returns:
        bool: True если обработка успешна
        
    Raises:
        ValueError: При неподдерживаемом формате
        Exception: При других ошибках обработки
    """
    start_time = time.time()
    try:
        logger.info(f"Начало обработки видео {file_path} (ID: {file_id})")
        
        # Проверяем формат
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        
        if not any(fmt.lower() in file_type for fmt in current_app.config['ALLOWED_VIDEO_FORMATS']):
            error_msg = f'Неподдерживаемый формат видео: {file_type}'
            logger.error(error_msg)
            update_file_status(file_id, processed=False, error=error_msg)
            raise ValueError(error_msg)
        
        # Создаем превью
        preview_path = Path(file_path).with_name(f'thumb_{Path(file_path).stem}.jpg')
        
        # Извлекаем первый кадр
        subprocess.run([
            'ffmpeg', '-i', file_path,
            '-vframes', '1',
            '-vf', f'scale={current_app.config["THUMBNAIL_SIZE"][0]}:{current_app.config["THUMBNAIL_SIZE"][1]}',
            str(preview_path)
        ], check=True)
        
        # Обновляем информацию о файле
        update_file_status(file_id, thumbnail_path=str(preview_path))
        
        processing_time = time.time() - start_time
        logger.info(f"Видео успешно обработано (ID: {file_id}, время: {processing_time:.2f}с)")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обработке видео {file_path}: {str(e)}")
        update_file_status(file_id, processed=False, error=str(e))
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(f"Превышено максимальное количество попыток обработки видео {file_path}")
            raise

@shared_task(bind=True, max_retries=3, default_retry_delay=300, base=BaseTask)
def cleanup_unused_files(self) -> bool:
    """
    Удаляет неиспользуемые файлы.
    
    Returns:
        bool: True если очистка успешна
        
    Raises:
        Exception: При ошибках очистки
    """
    start_time = time.time()
    try:
        logger.info("Начало очистки неиспользуемых файлов")
        
        # Получаем все файлы, которые не привязаны к постам
        unused_files = File.query.filter_by(post_id=None).all()
        deleted_count = 0
        error_count = 0
        
        for file in unused_files:
            try:
                logger.info(f"Удаление неиспользуемого файла {file.file_path}")
                # Удаляем файл и его превью
                if os.path.exists(file.file_path):
                    os.remove(file.file_path)
                if file.thumbnail_path and os.path.exists(file.thumbnail_path):
                    os.remove(file.thumbnail_path)
                
                # Удаляем запись из базы данных
                db.session.delete(file)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Ошибка при удалении файла {file.file_path}: {str(e)}")
                error_count += 1
        
        db.session.commit()
        cleanup_time = time.time() - start_time
        logger.info(f"Очистка завершена: удалено {deleted_count} файлов, ошибок: {error_count}, "
                   f"время: {cleanup_time:.2f}с")
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке неиспользуемых файлов: {str(e)}")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error("Превышено максимальное количество попыток очистки файлов")
            raise 
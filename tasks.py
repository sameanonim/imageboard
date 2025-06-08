from celery import shared_task
from PIL import Image
import os
from pathlib import Path
from flask import current_app
import magic
import subprocess
from models import db, File

@shared_task
def process_image(file_path, file_id):
    """Обрабатывает загруженное изображение."""
    try:
        # Открываем изображение
        with Image.open(file_path) as img:
            # Проверяем формат
            if img.format not in current_app.config['ALLOWED_IMAGE_FORMATS']:
                raise ValueError(f'Неподдерживаемый формат изображения: {img.format}')
            
            # Изменяем размер, если нужно
            if img.size[0] > current_app.config['MAX_IMAGE_SIZE'][0] or \
               img.size[1] > current_app.config['MAX_IMAGE_SIZE'][1]:
                img.thumbnail(current_app.config['MAX_IMAGE_SIZE'])
            
            # Сохраняем обработанное изображение
            img.save(file_path, optimize=True, quality=85)
            
            # Создаем превью
            preview_path = Path(file_path).with_name(f'thumb_{Path(file_path).name}')
            img.thumbnail(current_app.config['THUMBNAIL_SIZE'])
            img.save(preview_path, optimize=True, quality=85)
            
            # Обновляем информацию о файле в базе данных
            with current_app.app_context():
                file = File.query.get(file_id)
                if file:
                    file.processed = True
                    file.thumbnail_path = str(preview_path)
                    db.session.commit()
            
            return True
    except Exception as e:
        # В случае ошибки обновляем статус файла
        with current_app.app_context():
            file = File.query.get(file_id)
            if file:
                file.error = str(e)
                db.session.commit()
        raise

@shared_task
def process_video(file_path, file_id):
    """Обрабатывает загруженное видео."""
    try:
        # Проверяем формат
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        
        if not any(fmt.lower() in file_type for fmt in current_app.config['ALLOWED_VIDEO_FORMATS']):
            raise ValueError(f'Неподдерживаемый формат видео: {file_type}')
        
        # Создаем превью
        preview_path = Path(file_path).with_name(f'thumb_{Path(file_path).stem}.jpg')
        
        # Извлекаем первый кадр
        subprocess.run([
            'ffmpeg', '-i', file_path,
            '-vframes', '1',
            '-vf', f'scale={current_app.config["THUMBNAIL_SIZE"][0]}:{current_app.config["THUMBNAIL_SIZE"][1]}',
            str(preview_path)
        ], check=True)
        
        # Обновляем информацию о файле в базе данных
        with current_app.app_context():
            file = File.query.get(file_id)
            if file:
                file.processed = True
                file.thumbnail_path = str(preview_path)
                db.session.commit()
        
        return True
    except Exception as e:
        # В случае ошибки обновляем статус файла
        with current_app.app_context():
            file = File.query.get(file_id)
            if file:
                file.error = str(e)
                db.session.commit()
        raise

@shared_task
def cleanup_unused_files():
    """Удаляет неиспользуемые файлы."""
    try:
        with current_app.app_context():
            # Получаем все файлы, которые не привязаны к постам
            unused_files = File.query.filter_by(post_id=None).all()
            
            for file in unused_files:
                # Удаляем файл и его превью
                if os.path.exists(file.file_path):
                    os.remove(file.file_path)
                if file.thumbnail_path and os.path.exists(file.thumbnail_path):
                    os.remove(file.thumbnail_path)
                
                # Удаляем запись из базы данных
                db.session.delete(file)
            
            db.session.commit()
            return True
    except Exception as e:
        raise 
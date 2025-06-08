import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime, timedelta
from flask import current_app, session
from models import db, Thread, Post, Ban
import random
import string
import hashlib
from io import BytesIO
import uuid
import cv2
import re
import piexif

def allowed_file(filename):
    """Проверяет, является ли расширение файла разрешенным."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def is_video(filename):
    """Проверяет, является ли файл видео."""
    video_extensions = {'webm', 'mp4'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in video_extensions

def create_video_thumbnail(video_path, output_path):
    """Создает превью для видеофайла."""
    try:
        cap = cv2.VideoCapture(video_path)
        # Устанавливаем позицию для кадра
        cap.set(cv2.CAP_PROP_POS_MSEC, current_app.config['VIDEO_THUMBNAIL_FRAME'] * 1000)
        success, frame = cap.read()
        if success:
            # Конвертируем BGR в RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Создаем изображение из кадра
            img = Image.fromarray(frame)
            # Изменяем размер
            img.thumbnail(current_app.config['VIDEO_THUMBNAIL_SIZE'])
            # Сохраняем
            img.save(output_path, 'JPEG')
        cap.release()
        return success
    except Exception as e:
        current_app.logger.error(f"Ошибка при создании превью видео: {str(e)}")
        return False

def is_gif(filename):
    """Проверяет, является ли файл GIF-анимацией."""
    return filename.lower().endswith('.gif')

def clean_exif(image):
    """Очищает EXIF-данные из изображения."""
    try:
        # Создаем новое изображение без EXIF
        data = list(image.getdata())
        new_image = Image.new(image.mode, image.size)
        new_image.putdata(data)
        return new_image
    except Exception as e:
        current_app.logger.error(f"Ошибка при очистке EXIF: {str(e)}")
        return image

def process_gif(gif_path, output_path):
    """Обрабатывает GIF-анимацию, создавая превью из первого кадра."""
    try:
        with Image.open(gif_path) as img:
            # Берем первый кадр
            img.seek(0)
            # Создаем копию первого кадра
            first_frame = img.copy()
            # Изменяем размер
            first_frame.thumbnail(current_app.config['THUMBNAIL_SIZE'])
            # Сохраняем как JPEG
            first_frame.save(output_path, 'JPEG')
            return True
    except Exception as e:
        current_app.logger.error(f"Ошибка при обработке GIF: {str(e)}")
        return False

def save_file(file, post_id):
    """Сохраняет загруженный файл и создает превью."""
    if file and allowed_file(file.filename):
        # Генерируем уникальное имя файла
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        
        # Создаем пути для сохранения
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        thumbnail_path = os.path.join(current_app.config['THUMBNAIL_FOLDER'], filename)
        
        # Сохраняем файл
        file.save(file_path)
        
        # Создаем превью в зависимости от типа файла
        if is_video(filename):
            success = create_video_thumbnail(file_path, thumbnail_path)
            if not success:
                thumbnail_path = os.path.join(current_app.static_folder, 'img', 'video_placeholder.jpg')
        elif is_gif(filename):
            success = process_gif(file_path, thumbnail_path)
            if not success:
                thumbnail_path = os.path.join(current_app.static_folder, 'img', 'gif_placeholder.jpg')
        else:
            # Для обычных изображений создаем превью и очищаем EXIF
            img = Image.open(file_path)
            # Очищаем EXIF
            img = clean_exif(img)
            # Создаем превью
            img.thumbnail(current_app.config['THUMBNAIL_SIZE'])
            img.save(thumbnail_path, 'JPEG')
            # Сохраняем оригинал без EXIF
            img.save(file_path, 'JPEG')
        
        return {
            'filename': filename,
            'original_name': file.filename,
            'thumbnail': os.path.basename(thumbnail_path),
            'is_video': is_video(filename),
            'is_gif': is_gif(filename)
        }
    return None

def check_ban(ip_address):
    """Проверяет, забанен ли IP-адрес"""
    active_ban = Ban.query.filter_by(
        ip_address=ip_address,
        is_active=True
    ).first()
    
    if active_ban:
        if active_ban.expires_at and active_ban.expires_at < datetime.utcnow():
            # Бан истек
            active_ban.is_active = False
            db.session.commit()
            return None
        return active_ban
    
    return None

def cleanup_old_threads():
    """Удаляет старые треды"""
    max_age = current_app.config['MAX_THREAD_AGE_DAYS']
    cutoff_date = datetime.utcnow() - timedelta(days=max_age)
    
    old_threads = Thread.query.filter(
        Thread.created_at < cutoff_date,
        Thread.is_sticky == False
    ).all()
    
    for thread in old_threads:
        # Удаляем все файлы, связанные с тредом
        for post in thread.posts:
            for file in post.files:
                # Удаляем оригинальный файл
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Удаляем миниатюру, если она есть
                if file.thumbnail_filename:
                    thumb_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.thumbnail_filename)
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)
        
        # Удаляем тред и все связанные с ним записи
        db.session.delete(thread)
    
    db.session.commit()

def format_file_size(size_in_bytes):
    """Форматирует размер файла в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} TB"

def get_thread_stats(thread):
    """Возвращает статистику треда"""
    return {
        'post_count': thread.posts.count(),
        'file_count': sum(post.files.count() for post in thread.posts),
        'last_update': thread.updated_at,
        'is_active': (datetime.utcnow() - thread.updated_at).days < 14
    }

def sanitize_filename(filename):
    """Очищает имя файла от потенциально опасных символов"""
    # Оставляем только буквы, цифры, точки и дефисы
    safe_filename = ''.join(c for c in filename if c.isalnum() or c in '.-_')
    return safe_filename or 'unnamed_file'

def generate_tripcode(name, secret_key):
    # Генерируем трипкод на основе имени и секретного ключа
    tripcode = hashlib.sha256((name + secret_key).encode()).hexdigest()[:10]
    return tripcode

def generate_captcha():
    # Генерируем случайную строку из 6 символов
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # Сохраняем капчу в сессии
    session['captcha'] = captcha_text
    # Создаем изображение
    image = Image.new('RGB', (200, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    # Добавляем текст
    draw.text((50, 30), captcha_text, fill=(0, 0, 0))
    # Сохраняем в BytesIO
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

def verify_captcha(captcha_input):
    return captcha_input.upper() == session.get('captcha', '').upper() 
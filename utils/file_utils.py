import os
from werkzeug.utils import secure_filename
from flask import current_app
import magic

def allowed_file(filename):
    """Проверяет, разрешен ли тип файла для загрузки."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder='uploads'):
    """Сохраняет загруженный файл."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        return filename
    return None

def check_ban(user):
    """Проверяет, забанен ли пользователь."""
    if not user or not user.is_authenticated:
        return False
    return user.is_banned

def generate_captcha():
    """Генерирует капчу."""
    # TODO: Реализовать генерацию капчи
    return "test_captcha"

def verify_captcha(captcha_value):
    """Проверяет капчу."""
    # TODO: Реализовать проверку капчи
    return True

def generate_tripcode(password):
    """Генерирует трипкод из пароля."""
    # TODO: Реализовать генерацию трипкода
    return "tripcode" 
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import tarfile
import gzip
import json
from flask import current_app

def create_backup_dir():
    """Создает директорию для резервных копий, если она не существует."""
    backup_dir = Path(current_app.config['BACKUP_DIR'])
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def backup_database():
    """Создает резервную копию базы данных."""
    backup_dir = create_backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Получаем путь к базе данных
    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    # Создаем имя файла бэкапа
    backup_name = f'db_backup_{timestamp}.sqlite'
    backup_path = backup_dir / backup_name
    
    # Копируем файл базы данных
    shutil.copy2(db_path, backup_path)
    
    # Создаем сжатый архив
    gz_path = backup_path.with_suffix('.sqlite.gz')
    with open(backup_path, 'rb') as f_in:
        with gzip.open(gz_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Удаляем несжатый файл
    backup_path.unlink()
    
    return gz_path

def backup_files():
    """Создает резервную копию загруженных файлов."""
    backup_dir = create_backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Получаем путь к директории с файлами
    upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
    
    # Создаем имя файла бэкапа
    backup_name = f'files_backup_{timestamp}.tar.gz'
    backup_path = backup_dir / backup_name
    
    # Создаем сжатый архив
    with tarfile.open(backup_path, 'w:gz') as tar:
        tar.add(upload_dir, arcname='files')
    
    return backup_path

def create_backup():
    """Создает полную резервную копию (база данных + файлы)."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = create_backup_dir()
    
    # Создаем бэкапы
    db_backup = backup_database()
    files_backup = backup_files()
    
    # Создаем метаданные бэкапа
    metadata = {
        'timestamp': timestamp,
        'database': str(db_backup.name),
        'files': str(files_backup.name),
        'version': current_app.config['VERSION']
    }
    
    # Сохраняем метаданные
    metadata_path = backup_dir / f'backup_{timestamp}_metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return {
        'timestamp': timestamp,
        'database': db_backup,
        'files': files_backup,
        'metadata': metadata_path
    }

def list_backups():
    """Возвращает список доступных резервных копий."""
    backup_dir = create_backup_dir()
    backups = []
    
    # Ищем все файлы метаданных
    for metadata_file in backup_dir.glob('*_metadata.json'):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Проверяем наличие файлов бэкапа
            db_path = backup_dir / metadata['database']
            files_path = backup_dir / metadata['files']
            
            if db_path.exists() and files_path.exists():
                backups.append({
                    'timestamp': metadata['timestamp'],
                    'database': str(db_path),
                    'files': str(files_path),
                    'metadata': str(metadata_file),
                    'version': metadata.get('version', 'unknown')
                })
        except (json.JSONDecodeError, KeyError):
            continue
    
    return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

def restore_backup(timestamp):
    """Восстанавливает резервную копию."""
    backup_dir = create_backup_dir()
    metadata_path = backup_dir / f'backup_{timestamp}_metadata.json'
    
    if not metadata_path.exists():
        raise FileNotFoundError('Резервная копия не найдена')
    
    # Загружаем метаданные
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Восстанавливаем базу данных
    db_path = backup_dir / metadata['database']
    if not db_path.exists():
        raise FileNotFoundError('Файл резервной копии базы данных не найден')
    
    # Распаковываем базу данных
    db_restore_path = Path(current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    with gzip.open(db_path, 'rb') as f_in:
        with open(db_restore_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Восстанавливаем файлы
    files_path = backup_dir / metadata['files']
    if not files_path.exists():
        raise FileNotFoundError('Файл резервной копии файлов не найден')
    
    # Распаковываем файлы
    upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
    with tarfile.open(files_path, 'r:gz') as tar:
        tar.extractall(path=upload_dir.parent)
    
    return True

def delete_backup(timestamp):
    """Удаляет резервную копию."""
    backup_dir = create_backup_dir()
    metadata_path = backup_dir / f'backup_{timestamp}_metadata.json'
    
    if not metadata_path.exists():
        raise FileNotFoundError('Резервная копия не найдена')
    
    # Загружаем метаданные
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Удаляем файлы
    db_path = backup_dir / metadata['database']
    files_path = backup_dir / metadata['files']
    
    if db_path.exists():
        db_path.unlink()
    if files_path.exists():
        files_path.unlink()
    if metadata_path.exists():
        metadata_path.unlink()
    
    return True 
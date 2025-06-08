from typing import Optional, List, Any, Dict, Set, Union, TypeVar, Generic
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declared_attr

logger = logging.getLogger(__name__)
db = SQLAlchemy()

T = TypeVar('T')

class BaseModel(db.Model):
    """Базовый класс для всех моделей."""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Получение имени таблицы из имени класса."""
        return cls.__name__.lower() + 's'
    
    def save(self) -> None:
        """Сохранение объекта в базу данных."""
        db.session.add(self)
        db.session.commit()
    
    def delete(self) -> None:
        """Удаление объекта из базы данных."""
        db.session.delete(self)
        db.session.commit()
    
    @classmethod
    def get_by_id(cls: T, id: int) -> Optional[T]:
        """
        Получение объекта по ID.
        
        Args:
            id: ID объекта
            
        Returns:
            Optional[T]: Объект или None
        """
        return cls.query.get(id)

class User(UserMixin, BaseModel):
    """
    Модель пользователя.
    
    Attributes:
        username: Имя пользователя
        email: Email пользователя
        password_hash: Хеш пароля
        is_superadmin: Является ли супер-администратором
        is_banned: Забанен ли пользователь
        ban_reason: Причина бана
        last_seen: Последний визит
        two_factor_secret: Секрет для 2FA
        two_factor_enabled: Включена ли 2FA
    """
    __table_args__ = (
        db.Index('idx_users_username', 'username'),
        db.Index('idx_users_email', 'email'),
        db.Index('idx_users_created_at', 'created_at')
    )
    
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 2FA поля
    two_factor_secret = db.Column(db.String(32))
    two_factor_enabled = db.Column(db.Boolean, default=False)
    
    posts = relationship('Post', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    achievements = relationship(
        'Achievement',
        secondary='user_achievements',
        backref=db.backref('users', lazy='dynamic')
    )

    def __init__(self, username: str, email: str, password: str) -> None:
        """
        Инициализация пользователя.
        
        Args:
            username: Имя пользователя
            email: Email пользователя
            password: Пароль пользователя
        """
        self.username = username
        self.email = email
        self.set_password(password)

    @validates('email')
    def validate_email(self, key: str, email: str) -> str:
        """
        Валидация email.
        
        Args:
            key: Ключ поля
            email: Email для валидации
            
        Returns:
            str: Валидный email
            
        Raises:
            ValueError: Если email невалидный
        """
        if not '@' in email:
            raise ValueError('Invalid email address')
        return email

    def set_password(self, password: str) -> None:
        """
        Установка пароля пользователя.
        
        Args:
            password: Новый пароль
        """
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password: str) -> bool:
        """
        Проверка пароля пользователя.
        
        Args:
            password: Пароль для проверки
            
        Returns:
            bool: True если пароль верный
        """
        return check_password_hash(self.password_hash, password)
    
    def enable_2fa(self, secret: str) -> None:
        """
        Включение двухфакторной аутентификации.
        
        Args:
            secret: Секретный ключ для 2FA
        """
        self.two_factor_secret = secret
        self.two_factor_enabled = True
        self.save()
    
    def disable_2fa(self) -> None:
        """Отключение двухфакторной аутентификации."""
        self.two_factor_secret = None
        self.two_factor_enabled = False
        self.save()
    
    def is_2fa_enabled(self) -> bool:
        """
        Проверка включена ли 2FA.
        
        Returns:
            bool: True если 2FA включена
        """
        return self.two_factor_enabled and self.two_factor_secret is not None

    def update_last_seen(self) -> None:
        """Обновление времени последнего визита."""
        self.last_seen = datetime.utcnow()
        self.save()

    def __repr__(self) -> str:
        return f'<User {self.username}>'

class Board(BaseModel):
    """
    Модель доски.
    
    Attributes:
        name: Короткое имя доски
        title: Полное название доски
        description: Описание доски
        is_locked: Заблокирована ли доска
        is_hidden: Скрыта ли доска
    """
    name = db.Column(db.String(8), unique=True, nullable=False)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    is_locked = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)
    
    threads = relationship('Thread', backref='board', lazy='dynamic',
                         cascade='all, delete-orphan')

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """
        Валидация имени доски.
        
        Args:
            key: Ключ поля
            name: Имя для валидации
            
        Returns:
            str: Валидное имя
            
        Raises:
            ValueError: Если имя невалидное
        """
        if len(name) < 2 or len(name) > 8:
            raise ValueError('Board name must be between 2 and 8 characters')
        return name.lower()

    def __repr__(self) -> str:
        return f'<Board {self.name}>'

class Thread(BaseModel):
    """
    Модель треда.
    
    Attributes:
        board_id: ID доски
        subject: Тема треда
        content: Содержание первого поста
        name: Имя автора
        updated_at: Дата обновления
        reply_count: Количество ответов
        last_reply_at: Дата последнего ответа
        is_archived: Архивирован ли тред
        archived_at: Дата архивации
        archive_reason: Причина архивации
        is_locked: Заблокирован ли тред
        is_pinned: Закреплен ли тред
        views: Количество просмотров
    """
    __table_args__ = (
        db.Index('idx_threads_created_at', 'created_at'),
        db.Index('idx_threads_is_locked', 'is_locked'),
        db.Index('idx_threads_is_pinned', 'is_pinned')
    )
    
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'), nullable=False)
    subject = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(50))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reply_count = db.Column(db.Integer, default=0)
    last_reply_at = db.Column(db.DateTime)
    is_archived = db.Column(db.Boolean, default=False)
    archived_at = db.Column(db.DateTime)
    archive_reason = db.Column(db.String(200))
    is_locked = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    
    board = relationship('Board', backref=db.backref('threads', lazy=True))
    posts = relationship('Post', backref='thread', lazy='dynamic', cascade='all, delete-orphan')
    files = relationship('File', backref='thread', lazy=True, cascade='all, delete-orphan')

    def __init__(self, subject: str) -> None:
        """
        Инициализация треда.
        
        Args:
            subject: Тема треда
        """
        self.subject = subject

    def increment_views(self) -> None:
        """Увеличение счетчика просмотров."""
        self.views += 1
        self.save()

    def lock(self) -> None:
        """Блокировка треда."""
        self.is_locked = True
        self.save()

    def unlock(self) -> None:
        """Разблокировка треда."""
        self.is_locked = False
        self.save()

    def pin(self) -> None:
        """Закрепление треда."""
        self.is_pinned = True
        self.save()

    def unpin(self) -> None:
        """Открепление треда."""
        self.is_pinned = False
        self.save()

    def archive(self, reason: str) -> None:
        """
        Архивирование треда.
        
        Args:
            reason: Причина архивации
        """
        self.is_archived = True
        self.archived_at = datetime.utcnow()
        self.archive_reason = reason
        self.save()

    def __repr__(self) -> str:
        return f'<Thread {self.subject}>'

class Post(BaseModel):
    """
    Модель поста.
    
    Attributes:
        thread_id: ID треда
        user_id: ID пользователя
        name: Имя автора
        tripcode: Трипкод
        ip_address: IP-адрес
        content: Содержание поста
        is_op: Является ли ОП
        report_count: Количество жалоб
        reply_to_id: ID поста, на который отвечают
    """
    __table_args__ = (
        db.Index('idx_posts_thread_id', 'thread_id'),
        db.Index('idx_posts_user_id', 'user_id'),
        db.Index('idx_posts_created_at', 'created_at'),
        db.Index('idx_posts_reply_to_id', 'reply_to_id')
    )
    
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(64))
    tripcode = db.Column(db.String(32))
    ip_address = db.Column(db.String(45))
    content = db.Column(db.Text)
    is_op = db.Column(db.Boolean, default=False)
    report_count = db.Column(db.Integer, default=0)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    
    files = relationship('File', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    replies = relationship(
        'Post',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    user = relationship('User', backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, content: str, thread_id: int, name: str, 
                 tripcode: Optional[str], ip_address: str, 
                 reply_to_id: Optional[int] = None) -> None:
        """
        Инициализация поста.
        
        Args:
            content: Содержание поста
            thread_id: ID треда
            name: Имя автора
            tripcode: Трипкод
            ip_address: IP-адрес
            reply_to_id: ID поста, на который отвечают
        """
        self.content = content
        self.thread_id = thread_id
        self.name = name
        self.tripcode = tripcode
        self.ip_address = ip_address
        self.reply_to_id = reply_to_id

    def increment_report_count(self) -> None:
        """Увеличение счетчика жалоб."""
        self.report_count += 1
        self.save()

    def __repr__(self) -> str:
        return f'<Post {self.id}>'

class File(BaseModel):
    """
    Модель файла.
    
    Attributes:
        post_id: ID поста
        filename: Имя файла
        original_filename: Оригинальное имя файла
        file_path: Путь к файлу
        thumbnail_path: Путь к превью
        file_size: Размер файла
        mime_type: MIME-тип
        processed: Обработан ли файл
        error: Ошибка обработки
        last_modified: Дата последнего изменения
    """
    __table_args__ = (
        db.Index('idx_files_post_id', 'post_id'),
        db.Index('idx_files_created_at', 'created_at'),
        db.Index('idx_files_mime_type', 'mime_type')
    )
    
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255))
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    processed = db.Column(db.Boolean, default=False)
    error = db.Column(db.Text)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = relationship('Post', backref=db.backref('files', lazy=True))

    def __init__(self, filename: str, original_filename: str, 
                 mime_type: str, size: int, path: str, post_id: int) -> None:
        """
        Инициализация файла.
        
        Args:
            filename: Имя файла
            original_filename: Оригинальное имя файла
            mime_type: MIME-тип
            size: Размер файла
            path: Путь к файлу
            post_id: ID поста
        """
        self.filename = filename
        self.original_filename = original_filename
        self.mime_type = mime_type
        self.file_size = size
        self.file_path = path
        self.post_id = post_id

    @property
    def is_image(self) -> bool:
        """
        Проверка является ли файл изображением.
        
        Returns:
            bool: True если файл изображение
        """
        return self.mime_type.startswith('image/')

    @property
    def is_video(self) -> bool:
        """
        Проверка является ли файл видео.
        
        Returns:
            bool: True если файл видео
        """
        return self.mime_type.startswith('video/')

    @property
    def is_processed(self) -> bool:
        """
        Проверка обработан ли файл.
        
        Returns:
            bool: True если файл обработан
        """
        return self.processed and not self.error

    @property
    def has_error(self) -> bool:
        """
        Проверка есть ли ошибка обработки.
        
        Returns:
            bool: True если есть ошибка
        """
        return bool(self.error)

    def delete(self) -> None:
        """Удаление файла и его превью."""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            if self.thumbnail_path and os.path.exists(self.thumbnail_path):
                os.remove(self.thumbnail_path)
            super().delete()
        except Exception as e:
            logger.error(f'Error deleting file {self.filename}: {e}')
            raise

    def __repr__(self) -> str:
        return f'<File {self.filename}>'

class Ban(BaseModel):
    """
    Модель бана.
    
    Attributes:
        ip_address: IP-адрес
        expires_at: Дата окончания
        is_active: Активен ли бан
    """
    ip_address = db.Column(db.String(45), nullable=False)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def is_expired(self) -> bool:
        """
        Проверка истек ли бан.
        
        Returns:
            bool: True если бан истек
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def deactivate(self) -> None:
        """Деактивация бана."""
        self.is_active = False
        self.save()

    def __repr__(self) -> str:
        return f'<Ban {self.ip_address}>'

class Report(BaseModel):
    """
    Модель жалобы.
    
    Attributes:
        post_id: ID поста
        reason: Причина жалобы
        ip_address: IP-адрес
        is_resolved: Решена ли жалоба
    """
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    reason = db.Column(db.Text)
    ip_address = db.Column(db.String(45), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    
    post = relationship('Post', backref=db.backref('reports', lazy='dynamic'))

    def resolve(self) -> None:
        """Решение жалобы."""
        self.is_resolved = True
        self.save()

    def __repr__(self) -> str:
        return f'<Report {self.id}>'

class Achievement(BaseModel):
    """
    Модель достижения.
    
    Attributes:
        name: Название достижения
        description: Описание достижения
        icon: Иконка достижения
        points: Очки за достижение
    """
    __table_args__ = (
        db.Index('idx_achievements_name', 'name'),
        db.Index('idx_achievements_points', 'points')
    )

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, default=0)

    def __init__(self, name: str, description: str, icon: str, points: int = 0) -> None:
        """
        Инициализация достижения.
        
        Args:
            name: Название достижения
            description: Описание достижения
            icon: Иконка достижения
            points: Очки за достижение
        """
        self.name = name
        self.description = description
        self.icon = icon
        self.points = points

    def __repr__(self) -> str:
        return f'<Achievement {self.name}>'

class UserAchievement(BaseModel):
    """
    Модель связи пользователя и достижения.
    
    Attributes:
        user_id: ID пользователя
        achievement_id: ID достижения
    """
    __table_args__ = (
        db.Index('idx_user_achievements_user_id', 'user_id'),
        db.Index('idx_user_achievements_achievement_id', 'achievement_id'),
        db.Index('idx_user_achievements_created_at', 'created_at')
    )

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)

    def __init__(self, user_id: int, achievement_id: int) -> None:
        """
        Инициализация связи пользователя и достижения.
        
        Args:
            user_id: ID пользователя
            achievement_id: ID достижения
        """
        self.user_id = user_id
        self.achievement_id = achievement_id

    def __repr__(self) -> str:
        return f'<UserAchievement {self.user_id}:{self.achievement_id}>'

# Регистрация обработчиков событий
@event.listens_for(Thread, 'after_insert')
def update_thread_count(mapper: Any, connection: Any, target: Thread) -> None:
    """Обновление счетчика тредов в доске."""
    connection.execute(
        "UPDATE boards SET thread_count = thread_count + 1 WHERE id = :board_id",
        {'board_id': target.board_id}
    )

@event.listens_for(Post, 'after_insert')
def update_post_count(mapper: Any, connection: Any, target: Post) -> None:
    """Обновление счетчика постов в треде."""
    connection.execute(
        "UPDATE threads SET reply_count = reply_count + 1, last_reply_at = :now WHERE id = :thread_id",
        {'thread_id': target.thread_id, 'now': datetime.utcnow()}
    ) 
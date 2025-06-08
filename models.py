from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging

logger = logging.getLogger(__name__)
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.Index('idx_users_username', 'username'),
        db.Index('idx_users_email', 'email'),
        db.Index('idx_users_created_at', 'created_at')
    )
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 2FA поля
    two_factor_secret = db.Column(db.String(32))
    two_factor_enabled = db.Column(db.Boolean, default=False)
    
    posts = db.relationship('Post', backref='user', lazy='dynamic')
    achievements = db.relationship(
        'Achievement',
        secondary='user_achievements',
        backref=db.backref('users', lazy='dynamic')
    )

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def enable_2fa(self, secret):
        self.two_factor_secret = secret
        self.two_factor_enabled = True
    
    def disable_2fa(self):
        self.two_factor_secret = None
        self.two_factor_enabled = False
    
    def is_2fa_enabled(self):
        return self.two_factor_enabled and self.two_factor_secret is not None

    def update_last_seen(self):
        self.last_seen = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

class Board(db.Model):
    __tablename__ = 'boards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(8), unique=True, nullable=False)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_locked = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)
    
    threads = db.relationship('Thread', backref='board', lazy='dynamic',
                            cascade='all, delete-orphan')

class Thread(db.Model):
    __tablename__ = 'threads'
    __table_args__ = (
        db.Index('idx_threads_created_at', 'created_at'),
        db.Index('idx_threads_is_locked', 'is_locked'),
        db.Index('idx_threads_is_pinned', 'is_pinned')
    )
    
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'), nullable=False)
    subject = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reply_count = db.Column(db.Integer, default=0)
    last_reply_at = db.Column(db.DateTime)
    is_archived = db.Column(db.Boolean, default=False)
    archived_at = db.Column(db.DateTime)
    archive_reason = db.Column(db.String(200))
    is_locked = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    
    board = db.relationship('Board', backref=db.backref('threads', lazy=True))
    posts = db.relationship('Post', backref='thread', lazy='dynamic')
    files = db.relationship('File', backref='thread', lazy=True, cascade='all, delete-orphan')

    def __init__(self, subject):
        self.subject = subject

    def increment_views(self):
        self.views += 1
        db.session.commit()

    def lock(self):
        self.is_locked = True
        db.session.commit()

    def unlock(self):
        self.is_locked = False
        db.session.commit()

    def pin(self):
        self.is_pinned = True
        db.session.commit()

    def unpin(self):
        self.is_pinned = False
        db.session.commit()

    def __repr__(self):
        return f'<Thread {self.subject}>'

class Post(db.Model):
    __tablename__ = 'posts'
    __table_args__ = (
        db.Index('idx_posts_thread_id', 'thread_id'),
        db.Index('idx_posts_user_id', 'user_id'),
        db.Index('idx_posts_created_at', 'created_at'),
        db.Index('idx_posts_reply_to_id', 'reply_to_id')
    )
    
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'), nullable=False)
    name = db.Column(db.String(64))
    tripcode = db.Column(db.String(32))
    ip_address = db.Column(db.String(45))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_op = db.Column(db.Boolean, default=False)
    report_count = db.Column(db.Integer, default=0)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    
    files = db.relationship('File', backref='post', lazy='dynamic')
    replies = db.relationship(
        'Post',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_user_id', 'user_id'),  # индекс на существующую колонку
    )

    def __init__(self, content, thread_id, name, tripcode, ip_address, reply_to_id=None):
        self.content = content
        self.thread_id = thread_id
        self.name = name
        self.tripcode = tripcode
        self.ip_address = ip_address
        self.user_id = user_id
        self.reply_to_id = reply_to_id
        self.user_id = user_id

    def __repr__(self):
        return f'<Post {self.id}>'

class File(db.Model):
    __tablename__ = 'files'
    __table_args__ = (
        db.Index('idx_files_post_id', 'post_id'),
        db.Index('idx_files_created_at', 'created_at'),
        db.Index('idx_files_mime_type', 'mime_type')
    )
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255))
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    processed = db.Column(db.Boolean, default=False)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('Post', backref=db.backref('files', lazy=True))
    
    def __init__(self, filename, original_filename, mime_type, size, path, post_id):
        self.filename = filename
        self.original_filename = original_filename
        self.mime_type = mime_type
        self.file_size = size
        self.file_path = path
        self.post_id = post_id

    @property
    def is_image(self):
        return self.mime_type.startswith('image/')
    
    @property
    def is_video(self):
        return self.mime_type.startswith('video/')
    
    @property
    def is_processed(self):
        return self.processed and not self.error
    
    @property
    def has_error(self):
        return bool(self.error)

    def delete(self):
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            if self.thumbnail_path and os.path.exists(self.thumbnail_path):
                os.remove(self.thumbnail_path)
            db.session.delete(self)
            db.session.commit()
            logger.info(f'File {self.id} deleted successfully')
        except Exception as e:
            logger.error(f'Error deleting file {self.id}: {str(e)}')
            db.session.rollback()
            raise

    def __repr__(self):
        return f'<File {self.filename}>'

class Ban(db.Model):
    __tablename__ = 'bans'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    reason = db.Column(db.Text)
    ip_address = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    
    post = db.relationship('Post', backref=db.backref('reports', lazy='dynamic'))

class Achievement(db.Model):
    __tablename__ = 'achievements'
    __table_args__ = (
        db.Index('idx_achievements_name', 'name'),
        db.Index('idx_achievements_points', 'points')
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, description, icon, points=0):
        self.name = name
        self.description = description
        self.icon = icon
        self.points = points

    def __repr__(self):
        return f'<Achievement {self.name}>'

class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    __table_args__ = (
        db.Index('idx_user_achievements_user_id', 'user_id'),
        db.Index('idx_user_achievements_achievement_id', 'achievement_id'),
        db.Index('idx_user_achievements_created_at', 'created_at')
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, achievement_id):
        self.user_id = user_id
        self.achievement_id = achievement_id

    def __repr__(self):
        return f'<UserAchievement {self.user_id} - {self.achievement_id}>' 
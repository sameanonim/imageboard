from typing import Optional, Callable, Any, Dict, Type
from flask import Flask, request, render_template, session, jsonify
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_cors import CORS
from config import BaseConfig, Config, redis_client
from models import db, User, Post
from filters import init_app as init_filters
from celery_config import make_celery
from utils.socket import init_socketio, socketio
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import text

# Инициализация расширений
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=Config.RATELIMIT_STORAGE_URL,
    strategy=Config.RATELIMIT_STRATEGY,
    default_limits=[Config.RATELIMIT_DEFAULT],
    headers_enabled=Config.RATELIMIT_HEADERS_ENABLED
)
celery = None
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': Config.REDIS_URL,
    'CACHE_DEFAULT_TIMEOUT': 300
})
socketio = None  # Инициализируем как None, будет установлено позже

def setup_logging(app: Flask) -> None:
    """
    Настройка логирования для приложения.
    
    Args:
        app: Flask приложение
    """
    if not app.debug and not app.testing:
        # Используем StreamHandler вместо RotatingFileHandler в контейнере
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
        stream_handler.setLevel(app.config['LOG_LEVEL'])
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(app.config['LOG_LEVEL'])
        app.logger.info('Imageboard startup')

def register_blueprints(app: Flask) -> None:
    """
    Регистрация всех blueprints приложения.
    
    Args:
        app: Flask приложение
    """
    from views.main import main as main_blueprint
    from views.auth import auth as auth_blueprint
    from views.admin import admin as admin_blueprint
    from views.api import api as api_blueprint
    from views.moderation import bp as moderation_blueprint
    
    blueprints = {
        'main': main_blueprint,
        'auth': (auth_blueprint, '/auth'),
        'admin': (admin_blueprint, '/admin'),
        'api': (api_blueprint, '/api'),
        'moderation': (moderation_blueprint, '/mod')
    }
    
    for name, blueprint in blueprints.items():
        if isinstance(blueprint, tuple):
            app.register_blueprint(blueprint[0], url_prefix=blueprint[1])
        else:
            app.register_blueprint(blueprint)
        app.logger.info(f'Registered blueprint: {name}')

def register_error_handlers(app: Flask) -> None:
    """
    Регистрация обработчиков ошибок.
    
    Args:
        app: Flask приложение
    """
    @app.errorhandler(404)
    def not_found_error(error: Any) -> tuple[str, int]:
        app.logger.warning(f'Page not found: {request.url} - {error}')
        return render_template('errors/404.html', achievements=[]), 404
    
    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple[str, int]:
        db.session.rollback()
        app.logger.error(f'Server Error: {error}', exc_info=True)
        return render_template('errors/500.html', achievements=[]), 500
    
    @app.errorhandler(403)
    def forbidden_error(error: Any) -> tuple[str, int]:
        app.logger.warning(f'Forbidden: {request.url} - {error}')
        return render_template('errors/403.html', achievements=[]), 403
        
    @app.errorhandler(Exception)
    def handle_exception(error: Exception) -> tuple[str, int]:
        db.session.rollback()
        app.logger.error(f'Unhandled Exception: {error}', exc_info=True)
        return render_template('errors/500.html', achievements=[]), 500

def init_extensions(app: Flask) -> None:
    """
    Инициализация расширений Flask.
    
    Args:
        app: Flask приложение
    """
    global socketio
    
    try:
        # Инициализация CORS
        CORS(app, 
             resources={r"/*": {"origins": app.config['CORS_ORIGINS']}},
             supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
             allow_headers=app.config['CORS_ALLOW_HEADERS'],
             expose_headers=app.config['CORS_EXPOSE_HEADERS'],
             methods=app.config['CORS_METHODS'])
        
        # Установка заголовков безопасности
        @app.after_request
        def add_security_headers(response):
            for header, value in app.config['SECURITY_HEADERS'].items():
                response.headers[header] = value
            return response
        
        # Инициализация базы данных
        db.init_app(app)
        migrate.init_app(app, db)
        
        # Инициализация аутентификации
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
        login_manager.login_message_category = 'info'
        
        # Инициализация локализации
        def get_locale():
            return session.get('language', app.config['BABEL_DEFAULT_LOCALE'])
        
        babel.init_app(app, locale_selector=get_locale)
        
        # Инициализация ограничителя запросов
        limiter.init_app(app)
        limiter.storage_uri = app.config['REDIS_URL']
        
        # Инициализация кэширования
        cache.init_app(app)
        
        # Инициализация Celery
        app.celery = make_celery(app)
        
        # Инициализация SocketIO
        init_socketio(app)
        
        app.logger.info('Initialized all extensions')
    except Exception as e:
        app.logger.error(f'Error initializing extensions: {str(e)}')
        raise

def create_app(config_class: Type[BaseConfig] = Config) -> Flask:
    """
    Создание и настройка приложения Flask.
    
    Args:
        config_class: Класс конфигурации приложения
        
    Returns:
        Flask: Настроенное приложение Flask
    """
    try:
        app = Flask(__name__)
        app.config.update(config_class.get_config())
        
        # Настройка логирования
        setup_logging(app)
        
        # Инициализация расширений
        init_extensions(app)
        
        # Эндпоинт проверки здоровья
        @app.route('/health')
        @limiter.exempt
        def health_check():
            try:
                # Проверка подключения к базе данных
                db.session.execute(db.text('SELECT 1'))
                # Проверка подключения к Redis
                redis_client.ping()
                return jsonify({'status': 'healthy'}), 200
            except Exception as e:
                app.logger.error(f'Health check failed: {str(e)}')
                return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
        
        # Обработка языка
        @app.before_request
        def before_request() -> None:
            """Обработка запроса перед его выполнением."""
            lang = request.args.get('lang')
            if lang and lang in ['ru', 'en']:
                session['language'] = lang
                
            # Обновляем last_seen для авторизованных пользователей
            if current_user.is_authenticated and hasattr(app, 'extensions') and 'sqlalchemy' in app.extensions:
                current_user.last_seen = datetime.utcnow()
                db.session.commit()
        
        # Добавление переменных в контекст шаблона
        @app.context_processor
        def inject_now():
            achievements = session.get('achievements', [])
            if not isinstance(achievements, list):
                achievements = []
            
            # Получаем количество онлайн пользователей и общее количество постов
            online_users = 0
            total_posts = 0
            
            if hasattr(app, 'extensions') and 'sqlalchemy' in app.extensions:
                try:
                    online_users = User.query.filter(User.last_seen >= datetime.utcnow() - timedelta(minutes=5)).count()
                    total_posts = Post.query.count()
                except Exception as e:
                    app.logger.error(f'Error getting statistics: {str(e)}')
            
            return {
                'now': datetime.utcnow(),
                'achievements': achievements,
                'online_users': online_users,
                'total_posts': total_posts
            }
        
        # Регистрация blueprints
        register_blueprints(app)
        
        # Регистрация фильтров
        init_filters(app)
        
        # Инициализация базы данных
        with app.app_context():
            try:
                # Проверяем, существует ли хотя бы одна таблица
                inspector = db.inspect(db.engine)
                existing_tables = inspector.get_table_names()
                
                if not existing_tables:
                    # Если таблиц нет, создаем все
                    db.create_all()
                    app.logger.info('Created all database tables')
                else:
                    # Если таблицы есть, проверяем каждую таблицу отдельно
                    for table in db.metadata.tables:
                        if table in existing_tables:
                            try:
                                # Начинаем транзакцию
                                with db.engine.begin() as conn:
                                    # Получаем все ограничения таблицы
                                    constraints = []
                                    
                                    # Получаем ограничения уникальности
                                    unique_constraints = inspector.get_unique_constraints(table)
                                    for constraint in unique_constraints:
                                        if isinstance(constraint, dict):
                                            constraints.append(constraint.get('name'))
                                    
                                    # Получаем внешние ключи
                                    foreign_keys = inspector.get_foreign_keys(table)
                                    for fk in foreign_keys:
                                        if isinstance(fk, dict):
                                            constraints.append(fk.get('name'))
                                    
                                    # Получаем первичные ключи
                                    pk_constraint = inspector.get_pk_constraint(table)
                                    if isinstance(pk_constraint, dict):
                                        constraints.append(pk_constraint.get('name'))
                                    
                                    # Получаем проверочные ограничения
                                    check_constraints = inspector.get_check_constraints(table)
                                    for constraint in check_constraints:
                                        if isinstance(constraint, dict):
                                            constraints.append(constraint.get('name'))
                                    
                                    # Удаляем все ограничения
                                    for constraint_name in constraints:
                                        if constraint_name:
                                            try:
                                                conn.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint_name}'))
                                                app.logger.info(f'Dropped existing constraint: {constraint_name}')
                                            except Exception as e:
                                                app.logger.warning(f'Could not drop constraint {constraint_name}: {str(e)}')
                                    
                                    # Создаем таблицу заново
                                    db.metadata.tables[table].create(conn, checkfirst=True)
                                    app.logger.info(f'Created table: {table}')
                            except Exception as e:
                                app.logger.error(f'Error processing table {table}: {str(e)}')
                                raise
            except Exception as e:
                app.logger.error(f'Error initializing database: {str(e)}')
                raise
        
        # Регистрация обработчиков ошибок
        register_error_handlers(app)
        
        # Регистрация CLI команд
        from cli import init_app as init_cli
        init_cli(app)
        
        app.logger.info('Application created successfully')
        return app
    except Exception as e:
        if 'app' in locals():
            app.logger.error(f'Error creating application: {str(e)}')
        raise

@login_manager.user_loader
def load_user(id: str) -> Optional[User]:
    """
    Загрузка пользователя для Flask-Login.
    
    Args:
        id: ID пользователя
        
    Returns:
        Optional[User]: Объект пользователя или None
    """
    return User.query.get(int(id))

def with_app_context(app: Flask, f: Callable) -> Callable:
    """
    Декоратор для выполнения функции в контексте приложения.
    
    Args:
        app: Flask приложение
        f: Функция для выполнения
        
    Returns:
        Callable: Обернутая функция
    """
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with app.app_context():
            return f(*args, **kwargs)
    return wrapper

app = create_app()

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=app.config['DEBUG']
    ) 
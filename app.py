from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from config import Config
from models import db, User
from views import main, admin, api
from views import moderation
from filters import init_app as init_filters
from celery_config import make_celery
from utils.socket import init_socketio
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()
limiter = Limiter(key_func=get_remote_address)
celery = None
cache = Cache()

def create_app(config_class=Config):
    """Создание и настройка приложения Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Настройка логирования
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/imageboard.log',
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Imageboard startup')
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    babel.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    
    # Инициализация Celery
    global celery
    celery = make_celery(app)
    
    # Инициализация SocketIO
    init_socketio(app)
    
    # Регистрация blueprints
    from views.main import main as main_blueprint
    from views.auth import auth as auth_blueprint
    from views.admin import admin as admin_blueprint
    from views.api import api as api_blueprint
    from views.moderation import moderation as moderation_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.register_blueprint(moderation_blueprint, url_prefix='/mod')
    
    # Регистрация фильтров
    init_filters(app)
    
    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    # Инициализация базы данных
    with app.app_context():
        db.create_all()
    
    # Регистрация CLI команд
    from cli import init_app as init_cli
    init_cli(app)
    
    return app

@babel.localeselector
def get_locale():
    """Определение языка интерфейса."""
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'ru')

@login_manager.user_loader
def load_user(id):
    """Загрузка пользователя для Flask-Login."""
    return User.query.get(int(id))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 
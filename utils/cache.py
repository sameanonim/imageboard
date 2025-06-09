from flask import current_app
from flask_caching import Cache
from models import Thread, Post
from sqlalchemy import func
from datetime import datetime, timedelta
from functools import wraps
import logging
import json

logger = logging.getLogger(__name__)
cache = Cache()

def init_cache(app):
    """Инициализация кэша."""
    try:
        if 'cache' not in app.extensions:
            cache.init_app(
                app,
                config={
                    'CACHE_TYPE': 'redis',
                    'CACHE_REDIS_URL': app.config['REDIS_URL'],
                    'CACHE_DEFAULT_TIMEOUT': 300,
                    'CACHE_KEY_PREFIX': 'imageboard_',
                    'CACHE_OPTIONS': {
                        'socket_timeout': 5,
                        'socket_connect_timeout': 5,
                        'retry_on_timeout': True
                    }
                }
            )
            app.extensions['cache'] = cache
            logger.info('Cache initialized successfully')
        else:
            logger.info('Cache already initialized')
    except Exception as e:
        logger.error(f'Error initializing cache: {str(e)}')
        raise

def cache_key_prefix():
    """Получение префикса для ключей кэша."""
    return f'imageboard_{datetime.utcnow().strftime("%Y%m%d")}_'

def cache_thread(thread_id, timeout=300):
    """Кэширование треда."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                key = f'{cache_key_prefix()}thread_{thread_id}'
                rv = cache.get(key)
                if rv is None:
                    rv = f(*args, **kwargs)
                    cache.set(key, rv, timeout=timeout)
                    logger.info(f'Thread {thread_id} cached')
                return rv
            except Exception as e:
                logger.error(f'Error caching thread {thread_id}: {str(e)}')
                return f(*args, **kwargs)
        return decorated_function
    return decorator

def cache_thread_list(timeout=60):
    """Кэширование списка тредов."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                key = f'{cache_key_prefix()}thread_list'
                rv = cache.get(key)
                if rv is None:
                    rv = f(*args, **kwargs)
                    cache.set(key, rv, timeout=timeout)
                    logger.info('Thread list cached')
                return rv
            except Exception as e:
                logger.error(f'Error caching thread list: {str(e)}')
                return f(*args, **kwargs)
        return decorated_function
    return decorator

def cache_user_profile(user_id, timeout=300):
    """Кэширование профиля пользователя."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                key = f'{cache_key_prefix()}user_{user_id}'
                rv = cache.get(key)
                if rv is None:
                    rv = f(*args, **kwargs)
                    cache.set(key, rv, timeout=timeout)
                    logger.info(f'User profile {user_id} cached')
                return rv
            except Exception as e:
                logger.error(f'Error caching user profile {user_id}: {str(e)}')
                return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_popular_threads():
    """Получает список популярных тредов из кэша или базы данных."""
    cache_key = current_app.config['POPULAR_THREADS_CACHE_KEY']
    threads = cache.get(cache_key)
    
    if threads is None:
        # Получаем треды за последние 24 часа
        day_ago = datetime.utcnow() - timedelta(days=1)
        threads = Thread.query.join(Post).filter(
            Post.created_at >= day_ago
        ).group_by(Thread.id).order_by(
            func.count(Post.id).desc()
        ).limit(
            current_app.config['POPULAR_THREADS_COUNT']
        ).all()
        
        # Кэшируем результат
        cache.set(
            cache_key,
            threads,
            timeout=current_app.config['THREAD_CACHE_TIMEOUT']
        )
    
    return threads

def invalidate_thread_cache(thread_id=None):
    """Инвалидирует кэш тредов."""
    if thread_id:
        # Инвалидируем кэш конкретного треда
        cache.delete(f'thread_{thread_id}')
    else:
        # Инвалидируем кэш популярных тредов
        cache.delete(current_app.config['POPULAR_THREADS_CACHE_KEY'])

def get_thread_from_cache(thread_id):
    """Получает тред из кэша или базы данных."""
    cache_key = f'thread_{thread_id}'
    thread = cache.get(cache_key)
    
    if thread is None:
        thread = Thread.query.get_or_404(thread_id)
        cache.set(
            cache_key,
            thread,
            timeout=current_app.config['THREAD_CACHE_TIMEOUT']
        )
    
    return thread

def invalidate_thread_list_cache():
    """Инвалидация кэша списка тредов."""
    try:
        key = f'{cache_key_prefix()}thread_list'
        cache.delete(key)
        logger.info('Thread list cache invalidated')
    except Exception as e:
        logger.error(f'Error invalidating thread list cache: {str(e)}')

def invalidate_user_profile_cache(user_id):
    """Инвалидация кэша профиля пользователя."""
    try:
        key = f'{cache_key_prefix()}user_{user_id}'
        cache.delete(key)
        logger.info(f'User profile {user_id} cache invalidated')
    except Exception as e:
        logger.error(f'Error invalidating user profile {user_id} cache: {str(e)}')

def clear_expired_cache():
    """Очистка устаревшего кэша."""
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        old_prefix = f'imageboard_{yesterday.strftime("%Y%m%d")}_'
        cache.delete_many([f'{old_prefix}*'])
        logger.info('Expired cache cleared')
    except Exception as e:
        logger.error(f'Error clearing expired cache: {str(e)}') 
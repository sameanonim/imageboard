from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
socketio = SocketIO()

def init_socketio(app):
    """Инициализация SocketIO."""
    try:
        socketio.init_app(
            app,
            message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'],
            async_mode=app.config['SOCKETIO_ASYNC_MODE'],
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True
        )
        logger.info('SocketIO initialized successfully')
    except Exception as e:
        logger.error(f'Error initializing SocketIO: {str(e)}')
        raise

@socketio.on('connect')
def handle_connect():
    """Обработка подключения клиента."""
    try:
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            emit('connected', {
                'status': 'connected',
                'user_id': current_user.id,
                'username': current_user.username
            })
            logger.info(f'User {current_user.id} connected')
    except Exception as e:
        logger.error(f'Error handling connect: {str(e)}')
        emit('error', {'message': 'Connection error'})

@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения клиента."""
    try:
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')
            logger.info(f'User {current_user.id} disconnected')
    except Exception as e:
        logger.error(f'Error handling disconnect: {str(e)}')

@socketio.on('join_thread')
def handle_join_thread(data):
    """Присоединение к комнате треда."""
    try:
        thread_id = data.get('thread_id')
        if thread_id and current_user.is_authenticated:
            join_room(f'thread_{thread_id}')
            logger.info(f'User {current_user.id} joined thread {thread_id}')
    except Exception as e:
        logger.error(f'Error joining thread: {str(e)}')
        emit('error', {'message': 'Error joining thread'})

@socketio.on('leave_thread')
def handle_leave_thread(data):
    """Выход из комнаты треда."""
    try:
        thread_id = data.get('thread_id')
        if thread_id and current_user.is_authenticated:
            leave_room(f'thread_{thread_id}')
            logger.info(f'User {current_user.id} left thread {thread_id}')
    except Exception as e:
        logger.error(f'Error leaving thread: {str(e)}')
        emit('error', {'message': 'Error leaving thread'})

def notify_new_post(thread_id, post):
    """Отправка уведомления о новом посте."""
    try:
        data = {
            'type': 'new_post',
            'thread_id': thread_id,
            'post_id': post.id,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'user': post.user.username,
            'created_at': post.created_at.isoformat()
        }
        socketio.emit('new_post', data, room=f'thread_{thread_id}')
        logger.info(f'New post notification sent for thread {thread_id}')
    except Exception as e:
        logger.error(f'Error sending new post notification: {str(e)}')

def notify_new_reply(thread_id, post, reply_to):
    """Отправка уведомления о новом ответе."""
    try:
        if reply_to and reply_to.user:
            data = {
                'type': 'new_reply',
                'thread_id': thread_id,
                'post_id': post.id,
                'reply_to_id': reply_to.id,
                'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
                'user': post.user.username,
                'created_at': post.created_at.isoformat()
            }
            socketio.emit('new_reply', data, room=f'user_{reply_to.user.id}')
            logger.info(f'New reply notification sent to user {reply_to.user.id}')
    except Exception as e:
        logger.error(f'Error sending new reply notification: {str(e)}')

def notify_thread_locked(thread_id, locked_by):
    """Отправка уведомления о блокировке треда."""
    try:
        data = {
            'type': 'thread_locked',
            'thread_id': thread_id,
            'locked_by': locked_by.username,
            'locked_at': datetime.utcnow().isoformat()
        }
        socketio.emit('thread_locked', data, room=f'thread_{thread_id}')
        logger.info(f'Thread locked notification sent for thread {thread_id}')
    except Exception as e:
        logger.error(f'Error sending thread locked notification: {str(e)}')

def notify_thread_unlocked(thread_id, unlocked_by):
    """Отправка уведомления о разблокировке треда."""
    try:
        data = {
            'type': 'thread_unlocked',
            'thread_id': thread_id,
            'unlocked_by': unlocked_by.username,
            'unlocked_at': datetime.utcnow().isoformat()
        }
        socketio.emit('thread_unlocked', data, room=f'thread_{thread_id}')
        logger.info(f'Thread unlocked notification sent for thread {thread_id}')
    except Exception as e:
        logger.error(f'Error sending thread unlocked notification: {str(e)}')

def notify_post_deleted(post):
    """Отправка уведомления об удалении поста."""
    try:
        if post.user:
            data = {
                'type': 'post_deleted',
                'post_id': post.id,
                'thread_id': post.thread_id,
                'deleted_at': datetime.utcnow().isoformat()
            }
            socketio.emit('post_deleted', data, room=f'user_{post.user.id}')
            logger.info(f'Post deleted notification sent to user {post.user.id}')
    except Exception as e:
        logger.error(f'Error sending post deleted notification: {str(e)}')

def notify_achievement(user, achievement):
    """Отправка уведомления о получении достижения."""
    try:
        data = {
            'type': 'achievement',
            'achievement_id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon,
            'received_at': datetime.utcnow().isoformat()
        }
        socketio.emit('achievement', data, room=f'user_{user.id}')
        logger.info(f'Achievement notification sent to user {user.id}')
    except Exception as e:
        logger.error(f'Error sending achievement notification: {str(e)}') 
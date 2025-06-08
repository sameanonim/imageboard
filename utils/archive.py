from datetime import datetime, timedelta
from models import Thread, db
from sqlalchemy import and_

def archive_old_threads(board_id=None, days=30, max_replies=1000, reason=None):
    """
    Архивирует старые треды.
    
    Args:
        board_id (int, optional): ID доски. Если None, архивирует на всех досках.
        days (int): Возраст треда в днях для архивации.
        max_replies (int): Максимальное количество ответов для архивации.
        reason (str): Причина архивации.
    """
    # Базовые условия для архивации
    conditions = [
        Thread.is_archived == False,
        Thread.created_at <= datetime.utcnow() - timedelta(days=days)
    ]
    
    # Добавляем условие по доске, если указана
    if board_id:
        conditions.append(Thread.board_id == board_id)
    
    # Находим треды для архивации
    threads = Thread.query.filter(and_(*conditions)).all()
    
    # Архивируем каждый тред
    for thread in threads:
        # Проверяем количество ответов
        if thread.reply_count >= max_replies:
            thread.is_archived = True
            thread.archived_at = datetime.utcnow()
            thread.archive_reason = reason or f'Архивирован автоматически: возраст {days} дней, {thread.reply_count} ответов'
    
    # Сохраняем изменения
    db.session.commit()
    
    return len(threads)

def unarchive_thread(thread_id, reason=None):
    """
    Разархивирует тред.
    
    Args:
        thread_id (int): ID треда.
        reason (str): Причина разархивации.
    """
    thread = Thread.query.get_or_404(thread_id)
    
    if not thread.is_archived:
        return False
    
    thread.is_archived = False
    thread.archived_at = None
    thread.archive_reason = reason or 'Разархивирован вручную'
    
    db.session.commit()
    return True

def get_archived_threads(board_id=None, page=1, per_page=20):
    """
    Получает список архивных тредов.
    
    Args:
        board_id (int, optional): ID доски. Если None, возвращает со всех досок.
        page (int): Номер страницы.
        per_page (int): Количество тредов на странице.
    """
    query = Thread.query.filter_by(is_archived=True)
    
    if board_id:
        query = query.filter_by(board_id=board_id)
    
    return query.order_by(Thread.archived_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    ) 
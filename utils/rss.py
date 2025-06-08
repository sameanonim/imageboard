from feedgen.feed import FeedGenerator
from datetime import datetime
from flask import url_for
from models import Thread, Post, Board

def generate_board_feed(board):
    """Генерирует RSS-ленту для доски."""
    fg = FeedGenerator()
    fg.title(f'/{board.name}/ - {board.description}')
    fg.link(href=url_for('main.board', board_id=board.id, _external=True))
    fg.description(f'Последние темы на доске /{board.name}/')
    fg.language('ru')
    
    # Получаем последние темы
    threads = Thread.query.filter_by(board_id=board.id)\
        .order_by(Thread.created_at.desc())\
        .limit(20).all()
    
    for thread in threads:
        fe = fg.add_entry()
        fe.title(thread.subject or 'Без темы')
        fe.link(href=url_for('main.thread', 
                           board_id=board.id, 
                           thread_id=thread.id, 
                           _external=True))
        fe.description(thread.content)
        fe.published(thread.created_at)
        fe.author(name=thread.name or 'Аноним')
    
    return fg.rss_str(pretty=True)

def generate_thread_feed(thread):
    """Генерирует RSS-ленту для треда."""
    fg = FeedGenerator()
    fg.title(f'/{thread.board.name}/ - {thread.subject}')
    fg.link(href=url_for('main.thread', 
                        board_id=thread.board_id, 
                        thread_id=thread.id, 
                        _external=True))
    fg.description(f'Обсуждение в теме "{thread.subject}"')
    fg.language('ru')
    
    # Получаем все сообщения в треде
    posts = Post.query.filter_by(thread_id=thread.id)\
        .order_by(Post.created_at.desc())\
        .limit(50).all()
    
    for post in posts:
        fe = fg.add_entry()
        fe.title(f'Ответ от {post.name or "Анонима"}')
        fe.link(href=url_for('main.thread', 
                           board_id=thread.board_id, 
                           thread_id=thread.id, 
                           _external=True) + f'#post-{post.id}')
        fe.description(post.content)
        fe.published(post.created_at)
        fe.author(name=post.name or 'Аноним')
    
    return fg.rss_str(pretty=True) 
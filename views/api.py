from flask import Blueprint, jsonify, request
from models import db, Board, Thread, Post, File
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy import desc
from utils import generate_tripcode

api = Blueprint('api', __name__)

@api.route('/api/boards')
def get_boards():
    """Получить список всех досок."""
    boards = Board.query.all()
    return jsonify([{
        'id': board.id,
        'name': board.name,
        'description': board.description,
        'is_nsfw': board.is_nsfw,
        'thread_count': Thread.query.filter_by(board_id=board.id).count()
    } for board in boards])

@api.route('/api/board/<int:board_id>')
def get_board(board_id):
    """Получить информацию о доске."""
    board = Board.query.get_or_404(board_id)
    return jsonify({
        'id': board.id,
        'name': board.name,
        'description': board.description,
        'is_nsfw': board.is_nsfw,
        'thread_count': Thread.query.filter_by(board_id=board.id).count()
    })

@api.route('/api/board/<int:board_id>/threads')
def get_board_threads(board_id):
    """Получить список тредов на доске."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort = request.args.get('sort', 'activity')
    
    query = Thread.query.filter_by(board_id=board_id)
    
    if sort == 'date':
        query = query.order_by(Thread.created_at.desc())
    elif sort == 'replies':
        query = query.order_by(Thread.reply_count.desc())
    else:  # activity
        query = query.order_by(Thread.last_reply_at.desc())
    
    threads = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'threads': [{
            'id': thread.id,
            'subject': thread.subject,
            'content': thread.content,
            'name': thread.name,
            'created_at': thread.created_at.isoformat(),
            'reply_count': thread.reply_count,
            'last_reply_at': thread.last_reply_at.isoformat() if thread.last_reply_at else None
        } for thread in threads.items],
        'total': threads.total,
        'pages': threads.pages,
        'current_page': threads.page
    })

@api.route('/api/thread/<int:thread_id>')
def get_thread(thread_id):
    """Получить информацию о треде."""
    thread = Thread.query.get_or_404(thread_id)
    return jsonify({
        'id': thread.id,
        'board_id': thread.board_id,
        'subject': thread.subject,
        'content': thread.content,
        'name': thread.name,
        'created_at': thread.created_at.isoformat(),
        'reply_count': thread.reply_count,
        'last_reply_at': thread.last_reply_at.isoformat() if thread.last_reply_at else None
    })

@api.route('/api/thread/<int:thread_id>/posts')
def get_thread_posts(thread_id):
    """Получить список сообщений в треде."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    posts = Post.query.filter_by(thread_id=thread_id)\
        .order_by(Post.created_at.asc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'posts': [{
            'id': post.id,
            'content': post.content,
            'name': post.name,
            'created_at': post.created_at.isoformat(),
            'files': [{
                'filename': file.filename,
                'original_name': file.original_name,
                'size': file.size,
                'width': file.width,
                'height': file.height,
                'thumbnail_url': file.thumbnail_url,
                'url': file.url
            } for file in post.files]
        } for post in posts.items],
        'total': posts.total,
        'pages': posts.pages,
        'current_page': posts.page
    })

@api.route('/api/thread/<int:thread_id>/posts', methods=['POST'])
def create_post(thread_id):
    """Создать новое сообщение в треде."""
    thread = Thread.query.get_or_404(thread_id)
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    content = data.get('content')
    name = data.get('name')
    tripcode = data.get('tripcode')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    if tripcode:
        name = f"{name or 'Аноним'}!{generate_tripcode(tripcode)}"
    
    post = Post(
        thread_id=thread_id,
        content=content,
        name=name
    )
    
    # TODO: Добавить обработку файлов
    
    thread.reply_count += 1
    thread.last_reply_at = datetime.utcnow()
    
    return jsonify({
        'id': post.id,
        'content': post.content,
        'name': post.name,
        'created_at': post.created_at.isoformat()
    }), 201

@api.route('/api/thread', methods=['POST'])
def create_thread():
    """Создать новый тред."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    board_id = data.get('board_id')
    subject = data.get('subject')
    content = data.get('content')
    name = data.get('name')
    tripcode = data.get('tripcode')
    
    if not all([board_id, content]):
        return jsonify({'error': 'Board ID and content are required'}), 400
    
    board = Board.query.get_or_404(board_id)
    
    if tripcode:
        name = f"{name or 'Аноним'}!{generate_tripcode(tripcode)}"
    
    thread = Thread(
        board_id=board_id,
        subject=subject,
        content=content,
        name=name
    )
    
    # TODO: Добавить обработку файлов
    
    return jsonify({
        'id': thread.id,
        'board_id': thread.board_id,
        'subject': thread.subject,
        'content': thread.content,
        'name': thread.name,
        'created_at': thread.created_at.isoformat()
    }), 201

@api.route('/post/<int:post_id>/preview')
def post_preview(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Форматируем дату
    date = post.created_at.strftime('%d.%m.%Y %H:%M')
    
    # Подготавливаем данные о файлах
    files = []
    if post.files:
        for file in post.files:
            file_data = {
                'name': file.original_name,
                'url': f'/static/uploads/{file.filename}',
                'thumbnail_url': f'/static/uploads/thumbnails/{file.thumbnail}',
                'is_video': file.is_video,
                'type': file.filename.split('.')[-1]
            }
            files.append(file_data)
    
    return jsonify({
        'author': post.name,
        'date': date,
        'content': post.content,
        'files': files
    }) 
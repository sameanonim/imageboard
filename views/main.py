from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify, g, abort
from flask_login import login_required, current_user
from models import db, Board, Thread, Post, File, User
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from forms import PostForm, SearchForm, ThreadForm
from utils import allowed_file, save_file, check_ban, generate_captcha, verify_captcha, generate_tripcode
from sqlalchemy import or_, desc
from utils.rss import generate_board_feed, generate_thread_feed
from utils.archive import get_archived_threads
from utils.achievements import check_achievements
from app import limiter
import magic
from celery import Celery
from utils.cache import get_popular_threads, get_thread_from_cache, invalidate_thread_cache
from utils.tasks import process_image, process_video
from utils.backup import create_backup, restore_backup, delete_backup, list_backups
from utils.socket import (
    notify_new_post, notify_new_reply, notify_thread_locked,
    notify_thread_unlocked, notify_post_deleted, notify_achievement
)
from utils.decorators import admin_required
import logging

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main.route('/')
def index():
    """Главная страница с популярными тредами."""
    try:
        threads = get_popular_threads()
        return render_template('index.html', threads=threads)
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        flash('Ошибка при загрузке страницы', 'error')
        return render_template('index.html', threads=[])

@main.route('/board/<string:board_id>')
def board(board_id):
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'date')
    board = Board.query.get_or_404(board_id)
    
    # Базовый запрос
    query = Thread.query.filter_by(board_id=board_id)
    
    # Применяем сортировку
    if sort == 'activity':
        # Сортировка по последнему обновлению
        query = query.order_by(Thread.is_sticky.desc(), Thread.last_updated.desc())
    elif sort == 'replies':
        # Сортировка по количеству ответов
        query = query.order_by(Thread.is_sticky.desc(), Thread.post_count.desc())
    else:  # sort == 'date'
        # Сортировка по дате создания
        query = query.order_by(Thread.is_sticky.desc(), Thread.created_at.desc())
    
    # Применяем пагинацию
    threads = query.paginate(page=page, per_page=current_app.config['THREADS_PER_PAGE'])
    
    return render_template('board.html', board=board, threads=threads)

@main.route('/<board_name>/thread/<int:thread_id>', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def thread(board_name, thread_id):
    board = Board.query.filter_by(name=board_name).first_or_404()
    thread = get_thread_from_cache(thread_id)
    form = PostForm()
    
    if form.validate_on_submit():
        post = Post(
            content=form.content.data,
            thread_id=thread_id,
            author=current_user if current_user.is_authenticated else None,
            tripcode=form.tripcode.data if form.tripcode.data else None
        )
        db.session.add(post)
        db.session.commit()
        
        # Проверяем достижения
        achievements = check_achievements(request.cookies)
        if achievements:
            response = redirect(url_for('main.thread', board_name=board_name, thread_id=thread_id))
            for achievement in achievements:
                response.set_cookie(
                    f'achievement_{achievement["id"]}',
                    'true',
                    max_age=31536000  # 1 год
                )
            return response
            
        # Инвалидируем кэш
        invalidate_thread_cache(thread_id)
        
        return redirect(url_for('main.thread', board_name=board_name, thread_id=thread_id))
    
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(thread_id=thread_id).order_by(Post.created_at.asc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE']
    )
    
    return render_template('thread.html', board=board, thread=thread, posts=posts, form=form)

@main.route('/<board_name>/new_thread', methods=['GET', 'POST'])
@limiter.limit("2 per minute", methods=["POST"])
def new_thread(board_name):
    board = Board.query.filter_by(name=board_name).first_or_404()
    form = PostForm()
    
    if form.validate_on_submit():
        thread = Thread(board_id=board.id)
        db.session.add(thread)
        db.session.flush()
        
        post = Post(
            thread_id=thread.id,
            name=form.name.data,
            subject=form.subject.data,
            content=form.content.data,
            author=current_user if current_user.is_authenticated else None,
            tripcode=form.tripcode.data if form.tripcode.data else None
        )
        db.session.add(post)
        db.session.commit()
        
        # Проверяем достижения
        check_achievements(current_user)
        
        # Инвалидируем кэш
        invalidate_thread_cache()
        
        return redirect(url_for('main.thread', board_name=board_name, thread_id=thread.id))
    
    return render_template('new_thread.html', board=board, form=form)

@main.route('/thread/<int:thread_id>/reply', methods=['POST'])
@login_required
def reply(thread_id):
    """Ответ в треде."""
    try:
        thread = get_thread_from_cache(thread_id)
        if not thread:
            abort(404)
        
        if thread.is_locked and not current_user.is_admin:
            flash('Тред заблокирован', 'error')
            return redirect(url_for('main.thread', thread_id=thread_id))
        
        form = PostForm()
        if form.validate_on_submit():
            post = Post(
                content=form.content.data,
                thread=thread,
                user=current_user
            )
            
            # Обработка файла
            if form.file.data:
                file = File(
                    filename=form.file.data.filename,
                    user=current_user
                )
                post.files.append(file)
                
                # Сохраняем файл
                file_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    file.filename
                )
                form.file.data.save(file_path)
                
                # Определяем тип файла и запускаем обработку
                mime_type = form.file.data.content_type
                if mime_type.startswith('image/'):
                    process_image.delay(file_path, file.id)
                elif mime_type.startswith('video/'):
                    process_video.delay(file_path, file.id)
            
            # Сохраняем пост
            thread.posts.append(post)
            thread.save()
            
            # Проверяем достижения
            achievements = check_achievements(current_user)
            for achievement in achievements:
                notify_achievement(current_user, achievement)
            
            # Отправляем уведомления
            notify_new_post(thread_id, post)
            if form.reply_to.data:
                reply_to = Post.query.get(form.reply_to.data)
                if reply_to:
                    notify_new_reply(thread_id, post, reply_to)
            
            # Инвалидируем кэш
            invalidate_thread_cache(thread_id)
            
            flash('Ответ добавлен', 'success')
            return redirect(url_for('main.thread', thread_id=thread_id))
        
        return render_template('thread.html', thread=thread, form=form)
    except Exception as e:
        logger.error(f"Error posting reply in thread {thread_id}: {str(e)}")
        flash('Ошибка при добавлении ответа', 'error')
        return redirect(url_for('main.thread', thread_id=thread_id))

@main.route('/thread/<int:thread_id>/lock', methods=['POST'])
@login_required
@admin_required
def lock_thread(thread_id):
    """Блокировка треда."""
    try:
        thread = get_thread_from_cache(thread_id)
        if not thread:
            abort(404)
        
        thread.is_locked = True
        thread.save()
        
        # Отправляем уведомление
        notify_thread_locked(thread_id, current_user)
        
        # Инвалидируем кэш
        invalidate_thread_cache(thread_id)
        
        flash('Тред заблокирован', 'success')
        return redirect(url_for('main.thread', thread_id=thread_id))
    except Exception as e:
        logger.error(f"Error locking thread {thread_id}: {str(e)}")
        flash('Ошибка при блокировке треда', 'error')
        return redirect(url_for('main.thread', thread_id=thread_id))

@main.route('/thread/<int:thread_id>/unlock', methods=['POST'])
@login_required
@admin_required
def unlock_thread(thread_id):
    """Разблокировка треда."""
    try:
        thread = get_thread_from_cache(thread_id)
        if not thread:
            abort(404)
        
        thread.is_locked = False
        thread.save()
        
        # Отправляем уведомление
        notify_thread_unlocked(thread_id, current_user)
        
        # Инвалидируем кэш
        invalidate_thread_cache(thread_id)
        
        flash('Тред разблокирован', 'success')
        return redirect(url_for('main.thread', thread_id=thread_id))
    except Exception as e:
        logger.error(f"Error unlocking thread {thread_id}: {str(e)}")
        flash('Ошибка при разблокировке треда', 'error')
        return redirect(url_for('main.thread', thread_id=thread_id))

@main.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Удаление поста."""
    try:
        post = Post.query.get_or_404(post_id)
        thread_id = post.thread_id
        
        if not (current_user.is_admin or post.user_id == current_user.id):
            abort(403)
        
        # Отправляем уведомление
        notify_post_deleted(post)
        
        # Удаляем пост
        post.delete()
        
        # Инвалидируем кэш
        invalidate_thread_cache(thread_id)
        
        flash('Пост удален', 'success')
        return redirect(url_for('main.thread', thread_id=thread_id))
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {str(e)}")
        flash('Ошибка при удалении поста', 'error')
        return redirect(url_for('main.thread', thread_id=thread_id))

@main.route('/captcha')
def captcha():
    return send_file(generate_captcha(), mimetype='image/png')

@main.route('/search', methods=['GET'])
def search():
    form = SearchForm()
    
    # Заполняем список досок для выбора
    form.board.choices = [(b.id, b.name) for b in Board.query.all()]
    
    if request.args.get('query'):
        query = request.args.get('query')
        search_type = request.args.get('search_type', 'all')
        board_id = request.args.get('board')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Базовый запрос
        if search_type == 'thread':
            search_query = Thread.query
        elif search_type == 'content':
            search_query = Post.query
        else:
            # Поиск везде
            search_query = Thread.query.union(Post.query)
        
        # Применяем фильтры
        if board_id:
            search_query = search_query.filter_by(board_id=board_id)
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            search_query = search_query.filter(Thread.created_at >= date_from)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            search_query = search_query.filter(Thread.created_at <= date_to)
        
        # Поиск по тексту
        if search_type == 'subject':
            search_query = search_query.filter(Thread.subject.ilike(f'%{query}%'))
        elif search_type == 'content':
            search_query = search_query.filter(Post.content.ilike(f'%{query}%'))
        elif search_type == 'author':
            search_query = search_query.filter(or_(
                Thread.name.ilike(f'%{query}%'),
                Post.name.ilike(f'%{query}%')
            ))
        else:
            search_query = search_query.filter(or_(
                Thread.subject.ilike(f'%{query}%'),
                Post.content.ilike(f'%{query}%'),
                Thread.name.ilike(f'%{query}%'),
                Post.name.ilike(f'%{query}%')
            ))
        
        # Пагинация
        page = request.args.get('page', 1, type=int)
        results = search_query.paginate(
            page=page,
            per_page=20,
            error_out=False
        )
        
        # Форматируем результаты
        formatted_results = []
        for result in results.items:
            if isinstance(result, Thread):
                formatted_results.append({
                    'type': 'thread',
                    'title': result.subject,
                    'content': result.content,
                    'author': result.name,
                    'date': result.created_at.strftime('%d.%m.%Y %H:%M'),
                    'board': result.board.name,
                    'url': url_for('main.thread', board_id=result.board_id, thread_id=result.id)
                })
            else:
                formatted_results.append({
                    'type': 'post',
                    'title': f'Ответ в теме "{result.thread.subject}"',
                    'content': result.content,
                    'author': result.name,
                    'date': result.created_at.strftime('%d.%m.%Y %H:%M'),
                    'board': result.thread.board.name,
                    'url': url_for('main.thread', board_id=result.thread.board_id, thread_id=result.thread_id)
                })
        
        return render_template('search.html', form=form, results=formatted_results, pagination=results)
    
    return render_template('search.html', form=form)

@main.route('/board/<int:board_id>/rss')
def board_rss(board_id):
    """RSS-лента для доски."""
    board = Board.query.get_or_404(board_id)
    return send_file(
        generate_board_feed(board),
        mimetype='application/rss+xml',
        as_attachment=False,
        download_name=f'board_{board.name}.xml'
    )

@main.route('/board/<int:board_id>/thread/<int:thread_id>/rss')
def thread_rss(board_id, thread_id):
    """RSS-лента для треда."""
    thread = Thread.query.filter_by(
        board_id=board_id,
        id=thread_id
    ).first_or_404()
    
    return send_file(
        generate_thread_feed(thread),
        mimetype='application/rss+xml',
        as_attachment=False,
        download_name=f'thread_{thread_id}.xml'
    )

@main.route('/archive')
def archive():
    """Страница архивных тредов."""
    board_id = request.args.get('board', type=int)
    page = request.args.get('page', 1, type=int)
    
    board = None
    if board_id:
        board = Board.query.get_or_404(board_id)
    
    threads = get_archived_threads(
        board_id=board_id,
        page=page,
        per_page=20
    )
    
    boards = Board.query.all()
    
    return render_template('archive.html',
                         threads=threads,
                         board=board,
                         boards=boards)

@main.route('/set-language/<lang>')
def set_language(lang):
    if lang not in ['ru', 'en']:
        lang = 'ru'
    response = redirect(request.referrer or url_for('main.index'))
    response.set_cookie('language', lang, max_age=31536000)  # 1 год
    return response

@main.route('/set-theme', methods=['POST'])
def set_theme():
    theme = request.json.get('theme', 'light')
    if theme not in ['light', 'dark']:
        theme = 'light'
    response = jsonify({'success': True})
    response.set_cookie('theme', theme, max_age=31536000)  # 1 год
    return response

@main.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)

@main.route('/backup')
@login_required
def backup():
    """Страница управления резервными копиями."""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
        
    backups = list_backups()
    return render_template('backup.html', backups=backups)

@main.route('/backup/create', methods=['POST'])
@login_required
def create_backup():
    """Создает новую резервную копию."""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
        
    try:
        backup = create_backup()
        flash('Резервная копия успешно создана', 'success')
    except Exception as e:
        flash(f'Ошибка при создании резервной копии: {str(e)}', 'error')
        
    return redirect(url_for('main.backup'))

@main.route('/backup/restore/<timestamp>', methods=['POST'])
@login_required
def restore_backup(timestamp):
    """Восстанавливает резервную копию."""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
        
    try:
        restore_backup(timestamp)
        flash('Резервная копия успешно восстановлена', 'success')
    except Exception as e:
        flash(f'Ошибка при восстановлении резервной копии: {str(e)}', 'error')
        
    return redirect(url_for('main.backup'))

@main.route('/backup/delete/<timestamp>', methods=['POST'])
@login_required
def delete_backup(timestamp):
    """Удаляет резервную копию."""
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
        
    try:
        delete_backup(timestamp)
        flash('Резервная копия успешно удалена', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении резервной копии: {str(e)}', 'error')
        
    return redirect(url_for('main.backup')) 
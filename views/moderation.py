from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Report, Ban, Thread, Post
from datetime import datetime, timedelta

bp = Blueprint('moderation', __name__, url_prefix='/admin/mod')

# Проверка прав администратора
@bp.before_request
def require_admin():
    # Предотвращаем бесконечные редиректы
    if request.endpoint == 'static':
        return
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        flash('Доступ только для администраторов.', 'error')
        return redirect(url_for('main.index'))

# Главная страница панели модерации
@bp.route('/')
@login_required
def dashboard():
    report_page = request.args.get('report_page', 1, type=int)
    ban_page = request.args.get('ban_page', 1, type=int)

    reports = Report.query.order_by(Report.created_at.desc()).paginate(page=report_page, per_page=20)
    bans = Ban.query.order_by(Ban.created_at.desc()).paginate(page=ban_page, per_page=20)

    return render_template('moderation/dashboard.html', reports=reports, bans=bans)

# Удаление поста (и темы, если она пустая)
@bp.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    thread_id = post.thread_id

    db.session.delete(post)
    db.session.commit()

    # Проверка, остались ли посты в теме
    remaining_posts = Post.query.filter_by(thread_id=thread_id).count()
    if remaining_posts == 0:
        thread = Thread.query.get(thread_id)
        if thread:
            db.session.delete(thread)
            db.session.commit()
            flash(f'Пост №{post_id} и пустая тема №{thread_id} удалены.', 'success')
        else:
            flash(f'Пост №{post_id} удалён. (Тема не найдена)', 'success')
    else:
        flash(f'Пост №{post_id} удалён.', 'success')

    return redirect(url_for('moderation.dashboard'))

# Бан по IP
@bp.route('/ban_ip/<ip>', methods=['GET', 'POST'])
@login_required
def ban_ip(ip):
    if request.method == 'POST':
        reason = request.form.get('reason') or 'Модераторский бан'
        try:
            days = int(request.form.get('days', 1))
        except ValueError:
            days = 1

        existing_ban = Ban.query.filter_by(ip_address=ip, is_active=True).first()
        if existing_ban:
            flash(f'IP {ip} уже забанен.', 'error')
            return redirect(url_for('moderation.dashboard'))

        ban = Ban(
            ip_address=ip,
            reason=reason,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=days),
            is_active=True
        )
        db.session.add(ban)
        db.session.commit()

        flash(f'IP {ip} забанен на {days} дн. Причина: {reason}', 'success')
        return redirect(url_for('moderation.dashboard'))

    # GET: форма для бана
    return render_template('moderation/ban_form.html', ip=ip)

# Разбан по ID бана
@bp.route('/unban_ip/<int:ban_id>', methods=['POST'])
@login_required
def unban_ip(ban_id):
    ban = Ban.query.get_or_404(ban_id)

    if not ban.is_active:
        flash(f'Бан для IP {ban.ip_address} уже снят.', 'info')
        return redirect(url_for('moderation.dashboard'))

    ban.is_active = False
    db.session.commit()
    flash(f'Бан для IP {ban.ip_address} снят.', 'success')
    return redirect(url_for('moderation.dashboard'))
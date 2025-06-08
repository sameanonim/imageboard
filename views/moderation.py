from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Report, Ban, Thread, Post
from datetime import datetime, timedelta

bp = Blueprint('moderation', __name__, url_prefix='/admin/mod')

@bp.before_request
def require_admin():
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        flash('Доступ только для администраторов.', 'error')
        return redirect(url_for('main.index'))

@bp.route('/')
@login_required
def dashboard():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    bans = Ban.query.order_by(Ban.created_at.desc()).all()
    return render_template('moderation/dashboard.html', reports=reports, bans=bans)

@bp.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    thread_id = post.thread_id
    db.session.delete(post)
    db.session.commit()
    flash(f'Пост №{post_id} удалён.', 'success')
    return redirect(url_for('moderation.dashboard'))

@bp.route('/ban_ip/<ip>', methods=['POST'])
@login_required
def ban_ip(ip):
    # Баним на 1 день по умолчанию
    ban = Ban(ip_address=ip, reason='Модераторский бан', created_at=datetime.utcnow(),
              expires_at=datetime.utcnow() + timedelta(days=1), is_active=True)
    db.session.add(ban)
    db.session.commit()
    flash(f'IP {ip} забанен.', 'success')
    return redirect(url_for('moderation.dashboard'))

@bp.route('/unban_ip/<int:ban_id>', methods=['POST'])
@login_required
def unban_ip(ban_id):
    ban = Ban.query.get_or_404(ban_id)
    ban.is_active = False
    db.session.commit()
    flash(f'Бан для IP {ban.ip_address} снят.', 'success')
    return redirect(url_for('moderation.dashboard')) 
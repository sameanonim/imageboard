from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Board, Thread, Post, File, Admin, Ban, Report
from datetime import datetime, timedelta

admin = Blueprint('admin', __name__)

@admin.route('/')
@login_required
def index():
    if not current_user.is_superadmin:
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    return render_template('admin/index.html')

@admin.route('/boards')
@login_required
def boards():
    if not current_user.is_superadmin:
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    boards = Board.query.all()
    return render_template('admin/boards.html', boards=boards)

@admin.route('/boards/new', methods=['GET', 'POST'])
@login_required
def new_board():
    if not current_user.is_superadmin:
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        board = Board(
            name=request.form['name'],
            title=request.form['title'],
            description=request.form['description'],
            is_nsfw=bool(request.form.get('is_nsfw')),
            max_threads=int(request.form['max_threads']),
            max_posts_per_thread=int(request.form['max_posts_per_thread'])
        )
        db.session.add(board)
        db.session.commit()
        flash('Доска создана')
        return redirect(url_for('admin.boards'))
    
    return render_template('admin/new_board.html')

@admin.route('/boards/<int:board_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_board(board_id):
    if not current_user.is_superadmin:
        flash('Доступ запрещен')
        return redirect(url_for('main.index'))
    
    board = Board.query.get_or_404(board_id)
    
    if request.method == 'POST':
        board.title = request.form['title']
        board.description = request.form['description']
        board.is_nsfw = bool(request.form.get('is_nsfw'))
        board.is_locked = bool(request.form.get('is_locked'))
        board.max_threads = int(request.form['max_threads'])
        board.max_posts_per_thread = int(request.form['max_posts_per_thread'])
        db.session.commit()
        flash('Доска обновлена')
        return redirect(url_for('admin.boards'))
    
    return render_template('admin/edit_board.html', board=board)

@admin.route('/reports')
@login_required
def reports():
    reports = Report.query.filter_by(is_resolved=False).all()
    return render_template('admin/reports.html', reports=reports)

@admin.route('/reports/<int:report_id>/resolve', methods=['POST'])
@login_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.is_resolved = True
    report.resolved_at = datetime.utcnow()
    report.resolved_by = current_user.id
    db.session.commit()
    flash('Жалоба обработана')
    return redirect(url_for('admin.reports'))

@admin.route('/bans')
@login_required
def bans():
    bans = Ban.query.filter_by(is_active=True).all()
    return render_template('admin/bans.html', bans=bans)

@admin.route('/bans/new', methods=['GET', 'POST'])
@login_required
def new_ban():
    if request.method == 'POST':
        duration = int(request.form['duration'])
        ban = Ban(
            ip_address=request.form['ip_address'],
            reason=request.form['reason'],
            expires_at=datetime.utcnow() + timedelta(days=duration),
            admin_id=current_user.id
        )
        db.session.add(ban)
        db.session.commit()
        flash('Бан добавлен')
        return redirect(url_for('admin.bans'))
    
    return render_template('admin/new_ban.html')

@admin.route('/bans/<int:ban_id>/delete', methods=['POST'])
@login_required
def delete_ban(ban_id):
    ban = Ban.query.get_or_404(ban_id)
    ban.is_active = False
    db.session.commit()
    flash('Бан удален')
    return redirect(url_for('admin.bans')) 
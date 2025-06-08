from flask_login import current_user
from flask import redirect, url_for, flash
from functools import wraps


def admin_required(f):
    """
    Декоратор, ограничивающий доступ к маршруту только администраторам.
    Перенаправляет на главную с сообщением, если пользователь не админ.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Вы должны войти в систему.", "warning")
            return redirect(url_for('auth.login'))

        if not getattr(current_user, 'is_admin', False):
            flash("У вас нет доступа к этой странице.", "danger")
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)

    return decorated_function
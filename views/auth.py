from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User
from forms import LoginForm, TwoFactorSetupForm, TwoFactorVerifyForm, RegisterForm
from utils.two_factor import (
    generate_secret,
    generate_totp,
    verify_totp,
    generate_qr_code
)

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            if user.two_factor_enabled:
                session['user_id'] = user.id
                return redirect(url_for('auth.two_factor_verify'))
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.index'))
        flash('Неверное имя пользователя или пароль', 'error')
    return render_template('auth/login.html', form=form)

@auth.route('/two-factor-verify', methods=['GET', 'POST'])
def two_factor_verify():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user = User.query.get(session['user_id'])
    if not user or not user.two_factor_enabled:
        return redirect(url_for('auth.login'))
        
    form = TwoFactorVerifyForm()
    if form.validate_on_submit():
        if verify_totp(user.two_factor_secret, form.token.data):
            login_user(user)
            session.pop('user_id', None)
            return redirect(url_for('main.index'))
        flash('Неверный код подтверждения', 'error')
    return render_template('auth/two_factor_verify.html', form=form)

@auth.route('/two-factor-setup', methods=['GET', 'POST'])
@login_required
def two_factor_setup():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
        
    form = TwoFactorSetupForm()
    if form.validate_on_submit():
        if verify_totp(current_user.two_factor_secret, form.token.data):
            current_user.enable_2fa()
            db.session.commit()
            flash('Двухфакторная аутентификация успешно включена', 'success')
            return redirect(url_for('main.index'))
        flash('Неверный код подтверждения', 'error')
        
    if not current_user.two_factor_secret:
        secret = generate_secret()
        current_user.two_factor_secret = secret
        db.session.commit()
        
    totp = generate_totp(current_user.two_factor_secret)
    qr_code = generate_qr_code(totp)
    
    return render_template('auth/two_factor_setup.html', form=form, qr_code=qr_code)

@auth.route('/two-factor-disable', methods=['POST'])
@login_required
def two_factor_disable():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
        
    current_user.disable_2fa()
    db.session.commit()
    flash('Двухфакторная аутентификация отключена', 'success')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form) 
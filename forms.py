from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, Email, EqualTo, ValidationError, Regexp
from flask_wtf.file import FileAllowed, FileSize
from models import User
import re

def validate_password_strength(form, field):
    """Валидация сложности пароля."""
    password = field.data
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Пароль должен содержать хотя бы одну строчную букву')
    if not re.search(r'\d', password):
        raise ValidationError('Пароль должен содержать хотя бы одну цифру')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|,.<>\/?]', password):
        raise ValidationError('Пароль должен содержать хотя бы один специальный символ')

def validate_username(form, field):
    """Валидация имени пользователя."""
    username = field.data
    if not re.match(r'^[a-zA-Z0-9_-]{3,32}$', username):
        raise ValidationError('Имя пользователя может содержать только буквы, цифры, дефис и подчеркивание')
    if User.query.filter_by(username=username).first():
        raise ValidationError('Это имя пользователя уже занято')

def validate_tripcode(form, field):
    """Валидация трипкода."""
    if field.data:
        if not re.match(r'^[a-zA-Z0-9_-]{1,32}$', field.data):
            raise ValidationError('Трипкод может содержать только буквы, цифры, дефис и подчеркивание')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(),
        Length(min=3, max=32),
        validate_username
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=8, max=128),
        validate_password_strength
    ])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class PostForm(FlaskForm):
    name = StringField('Имя', validators=[
        Optional(),
        Length(max=50),
        Regexp(r'^[a-zA-Z0-9_-]{1,50}$', message='Имя может содержать только буквы, цифры, дефис и подчеркивание')
    ])
    tripcode = StringField('Трипкод', validators=[Optional(), validate_tripcode])
    content = TextAreaField('Сообщение', validators=[
        DataRequired(),
        Length(max=10000),
        Regexp(r'^[^<>]*$', message='HTML-теги запрещены')
    ])
    files = FileField('Файлы', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm'], 'Неподдерживаемый формат файла'),
        FileSize(max_size=10 * 1024 * 1024, message='Размер файла не должен превышать 10MB')
    ])
    captcha = StringField('Капча', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Неверный формат капчи')
    ])
    submit = SubmitField('Отправить')

class SearchForm(FlaskForm):
    query = StringField('Поиск', validators=[
        DataRequired(),
        Length(max=100),
        Regexp(r'^[^<>]*$', message='HTML-теги запрещены')
    ])
    search_type = SelectField('Тип поиска', 
                            choices=[
                                ('all', 'Везде'),
                                ('subject', 'В темах'),
                                ('content', 'В сообщениях'),
                                ('author', 'По автору')
                            ],
                            default='all')
    board = SelectField('Доска', validators=[Optional()])
    date_from = StringField('От даты', validators=[
        Optional(),
        Regexp(r'^\d{4}-\d{2}-\d{2}$', message='Неверный формат даты (YYYY-MM-DD)')
    ])
    date_to = StringField('До даты', validators=[
        Optional(),
        Regexp(r'^\d{4}-\d{2}-\d{2}$', message='Неверный формат даты (YYYY-MM-DD)')
    ])

class TwoFactorSetupForm(FlaskForm):
    token = StringField('Код подтверждения', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Код должен содержать 6 цифр'),
        Regexp(r'^\d{6}$', message='Код должен содержать только цифры')
    ])
    submit = SubmitField('Подтвердить')

class TwoFactorVerifyForm(FlaskForm):
    token = StringField('Код подтверждения', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Код должен содержать 6 цифр'),
        Regexp(r'^\d{6}$', message='Код должен содержать только цифры')
    ])
    submit = SubmitField('Войти')

class ThreadForm(FlaskForm):
    subject = StringField('Тема', validators=[
        DataRequired(),
        Length(max=100),
        Regexp(r'^[^<>]*$', message='HTML-теги запрещены')
    ])
    content = TextAreaField('Сообщение', validators=[
        DataRequired(),
        Length(max=10000),
        Regexp(r'^[^<>]*$', message='HTML-теги запрещены')
    ])
    name = StringField('Имя', validators=[
        Optional(),
        Length(max=50),
        Regexp(r'^[a-zA-Z0-9_-]{1,50}$', message='Имя может содержать только буквы, цифры, дефис и подчеркивание')
    ])
    tripcode = StringField('Трипкод', validators=[Optional(), validate_tripcode])
    files = FileField('Файлы', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm'], 'Неподдерживаемый формат файла'),
        FileSize(max_size=10 * 1024 * 1024, message='Размер файла не должен превышать 10MB')
    ])
    captcha = StringField('Капча', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Неверный формат капчи')
    ])
    submit = SubmitField('Создать тред')

class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(),
        Length(min=3, max=32),
        validate_username
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=8, max=128),
        validate_password_strength
    ])
    password2 = PasswordField('Подтвердите пароль', validators=[
        DataRequired(),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Зарегистрироваться') 
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, Email, EqualTo, ValidationError
from flask_wtf.file import FileAllowed
from models import User

class PostForm(FlaskForm):
    name = StringField('Имя', validators=[Optional(), Length(max=50)])
    tripcode = StringField('Трипкод', validators=[Optional(), Length(max=32)])
    content = TextAreaField('Сообщение', validators=[DataRequired(), Length(max=10000)])
    files = FileField('Файлы', validators=[Optional()])
    captcha = StringField('Капча', validators=[DataRequired()])
    submit = SubmitField('Отправить')

class SearchForm(FlaskForm):
    query = StringField('Поиск', validators=[DataRequired(), Length(max=100)])
    search_type = SelectField('Тип поиска', 
                            choices=[
                                ('all', 'Везде'),
                                ('subject', 'В темах'),
                                ('content', 'В сообщениях'),
                                ('author', 'По автору')
                            ],
                            default='all')
    board = SelectField('Доска', validators=[Optional()])
    date_from = StringField('От даты', validators=[Optional()])
    date_to = StringField('До даты', validators=[Optional()])

class TwoFactorSetupForm(FlaskForm):
    token = StringField('Код подтверждения', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Код должен содержать 6 цифр')
    ])
    submit = SubmitField('Подтвердить')

class TwoFactorVerifyForm(FlaskForm):
    token = StringField('Код подтверждения', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Код должен содержать 6 цифр')
    ])
    submit = SubmitField('Войти') 
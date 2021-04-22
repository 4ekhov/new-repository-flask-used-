from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class MapRequestForm(FlaskForm):
    coordinates = StringField('Координаты (долгота,широта)', validators=[DataRequired()])
    size = SelectField('Размер', choices=['1,1', '2,2', '3,3', '7,7', '15,15', '30,30', '58,58', '89,89'])
    type = SelectField('Тип карты', choices=['map', 'sat', 'skl', 'sat,skl'])
    add_to_sql = BooleanField('Сохранить для всех')
    recaptcha = RecaptchaField('Капча')
    submit = SubmitField('Смоделировать карту')


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')


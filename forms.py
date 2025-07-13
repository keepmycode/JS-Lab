from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User

class RegisterForm(FlaskForm):
    username = StringField(
        'Имя пользователя',
        validators=[
            DataRequired("Поле обязательно для заполнения"),
            Length(min=3, max=25, message="От 3 до 25 символов")
        ]
    )
    password = PasswordField(
        'Пароль',
        validators=[
            DataRequired("Поле обязательно для заполнения"),
            Length(min=6, message="Не менее 6 символов")
        ]
    )
    password2 = PasswordField(
        'Повторите пароль',
        validators=[
            DataRequired("Поле обязательно для заполнения"),
            EqualTo('password', message='Пароли должны совпадать')
        ]
    )
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя уже занято. Пожалуйста, выберите другое.')

class LoginForm(FlaskForm):
    username = StringField(
        'Имя пользователя',
        validators=[DataRequired("Поле обязательно для заполнения")]
    )
    password = PasswordField(
        'Пароль',
        validators=[DataRequired("Поле обязательно для заполнения")]
    )
    submit = SubmitField('Войти')

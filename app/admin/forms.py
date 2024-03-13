from collections.abc import Sequence
from typing import Any, Mapping
from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError
from wtforms import PasswordField
from wtforms.validators import DataRequired


class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    def validate_username(form, field):
        if field.data != current_app.config["ADMIN_USERNAME"]:
            raise ValidationError('Wrong credentials')
    
    def validate_password(form, field):
        if field.data != current_app.config["ADMIN_PASSWORD"]:
            raise ValidationError('Wrong credentials')

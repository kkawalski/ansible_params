from dataclasses import dataclass
from functools import wraps

from flask import (
    current_app,
    redirect,
    request,
    Response,
    url_for,
)
from werkzeug.datastructures import Authorization


@dataclass
class User:
    username: str
    password: str

def authenticate_admin(user: User, response: Response):
    if check_admin_creds(user):
        auth = Authorization("basic", {"username": user.username, "password": user.password})
        response.set_cookie("Authorization", auth.to_header())

def check_admin_creds(user: User):
    admin_username = current_app.config.get("ADMIN_USERNAME")
    admin_password = current_app.config.get("ADMIN_PASSWORD")

    return user.username == admin_username and user.password == admin_password

def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        authorization = request.cookies.get("Authorization")
        auth = Authorization.from_header(authorization)
        if authorization is None:
            return redirect(url_for("admin.login"))
        username = auth.username
        password = auth.password
        user = User(username, password)
        if not check_admin_creds(user):
            return redirect(url_for("admin.login"))
        return func(*args, **kwargs)
    return wrapper

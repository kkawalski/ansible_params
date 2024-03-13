from base64 import b64decode, b64encode
from flask import (
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from .auth import User, admin_only, authenticate_admin

from .forms import AdminLoginForm

from . import admin


@admin.route("/home")
@admin_only
def home():
    return "IMADMIN"

@admin.route("/login", methods=["GET", "POST"])
def login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        response = redirect(url_for('.home'))
        authenticate_admin(user, response)
        return response
    return render_template("admin/login.html", form=form)

@admin.route("/logout", methods=["GET", "POST"])
@admin_only
def logout():
    response = redirect(url_for("main.home"))
    response.delete_cookie("Authorization")
    return response

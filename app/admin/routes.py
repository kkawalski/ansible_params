from base64 import b64decode, b64encode
import os
from flask import (
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from app.utils import (
    allowed_params_file,
    form_to_params_list, 
    get_all_params_filenames, 
    get_params_filename, 
    read_params_file, 
    write_to_params_file
)
from .auth import User, admin_only, authenticate_admin
from .forms import AdminLoginForm
from . import admin


@admin.route("/home")
@admin_only
def home():
    return render_template("admin/menu.html")


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


@admin.route("/form-list", methods=["GET"])
@admin_only
def form_list():
    param_forms = get_all_params_filenames()
    return render_template("admin/form_list.html", param_forms=param_forms)

@admin.route("/change-form/<form_id>", methods=["GET", "POST"])
@admin_only
def change_form(form_id):
    if request.method == "POST":
        new_form = dict(request.form)
        new_params = form_to_params_list(new_form)
        write_to_params_file(new_params, form_id=form_id)
        return redirect(url_for(".change_form", form_id=form_id))

    params = read_params_file(form_id=form_id)
    return render_template("admin/change_form.html", params=params, form_id=form_id)

@admin.route("/new-form", methods=["GET", "POST"])
@admin_only
def new_form():
    if request.method == "POST":
        new_form = dict(request.form)
        form_id = new_form.pop("form_id")
        new_params = form_to_params_list(new_form)
        write_to_params_file(new_params, form_id=form_id)
        return redirect(url_for(".form_list"))
    return render_template("admin/new_form.html")

@admin.route("/upload-new-form", methods=["POST"])
@admin_only
def upload_new_form():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for(".new_form"))
    file = request.files['file']

    filename = file.filename
    form_id = request.form.get("form_id")
    if form_id:
        filename = f"{form_id}.json"

    if not filename:
        flash('No selected file', 'danger')
        return redirect(url_for(".new_form"))

    if  not (file and allowed_params_file(filename)):
        flash('Wrong file or extension', 'danger')
        return redirect(url_for(".new_form"))

    filename = secure_filename(filename)
    file.save(get_params_filename(filename))

    return redirect(url_for(".form_list"))

@admin.route("/delete-form", methods=["POST"])
@admin_only
def delete_form():
    form_id = request.json.get("formId")
    form_file = get_params_filename(form_id=form_id)
    if os.path.exists(form_file):
        os.remove(form_file)
    else:
        current_app.logger.info(f"The file {form_file} does not exist") 
    return jsonify({'status': 'ok'})


@admin.route("/upload-new-playbook", methods=["GET", "POST"])
@admin_only
def upolad_new_playbook():
    file = request.files['file']

    file.save(current_app.config["ANSIBLE_PLAYBOOK_FILE"])

    return redirect(url_for(".show_playbook"))

@admin.route("/show-playbook", methods=["GET"])
@admin_only
def show_playbook():
    filename = current_app.config["ANSIBLE_PLAYBOOK_FILE"]
    with open(current_app.config["ANSIBLE_PLAYBOOK_FILE"], "r") as playbook_file:
        content = playbook_file.read()
    line_count = content.count("\n") + 1
    return render_template(
        "admin/show_playbook.html", 
        file_content=content, 
        line_count=line_count,
        filename=filename.rsplit("/", 1)[-1]
    )

@admin.route("/download-playbook", methods=["GET"])
@admin_only
def download_playbook():
    return send_file(
        current_app.config["ANSIBLE_PLAYBOOK_FILE"], 
        mimetype="application/x-yaml",
        as_attachment=True,
    )



from typing import Any
import uuid
from flask import (
    current_app,
    g,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    Response,
    jsonify,
)

from . import main
from app import cache
from app.utils import (
    fill_ansible_params_file,
    get_all_params_filenames,
    get_thread_by_name,
    read_params_file,
    run_ansible,
    write_to_params_file,
    Param,
)


@main.after_request
def set_session_cookie(response: Response):
    if not request.cookies.get("session_id"):
        response.set_cookie("session_id", g.session_id)
        current_app.logger.info(f"Set cookie session_id: {g.session_id}")
    return response


@main.before_request
def load_session():
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    current_app.logger.info(f"Session id: {session_id}")
    g.session_id = session_id


@main.before_request
def load_params():
    if cache.has(g.session_id):
        params = cache.get(g.session_id)["params"]
        current_app.logger.info(f"Session params {params}")

    elif cache.has("params"):
        params = cache.get("params")
        current_app.logger.info(f"Cache params {params}")

    else:
        params = {"default": read_params_file(form_id="default")}
        cache.set("params", params)
        current_app.logger.info(f"Set new cache params from file {params}")

    g.params = params


@main.before_request
def session_cache_before_request():
    session_cache = cache.get(g.session_id) if cache.has(g.session_id) else "empty"
    current_app.logger.info(f"Session cache before request {session_cache}")


@main.after_request
def session_cache_after_request(response):
    session_cache = cache.get(g.session_id) if cache.has(g.session_id) else "empty"
    current_app.logger.info(f"Session cache after request {session_cache}")
    return response


@main.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@main.route("/form-choice", methods=["GET"])
def form_choice():
    choices = get_all_params_filenames()
    return render_template("main/choose.html", choices=choices)


@main.route("/fill-params", methods=["GET"])
def fill_params_default():
    return redirect(url_for(".fill_params", form_id="default"))


@main.route("/fill-params/<form_id>", methods=["GET", "POST"])
def fill_params(form_id):
    session_id = g.session_id
    params = g.params.get(form_id)
    if params is None:
        params = read_params_file(form_id=form_id)
        all_params = cache.get("params")
        all_params.update({form_id: params})
        cache.set("params", all_params)
        current_app.logger.info(f"Read params file {form_id}.json: {params}")
    
    if request.method == "POST":
        new_params_data = request.form
        new_params = [
            Param(name=name, defaultValue=value, description=params[i].description) 
            for i, (name, value) in enumerate(new_params_data.items())
        ]
        cache.set(session_id, {
            "params": {form_id: new_params},
            "form_id": form_id,
        })
        flash("Check params and click build", "info")
        return redirect(url_for(".build"))
    
    return render_template("main/fill.html", filename=params[0], params=params[1:])


@main.route("/build", methods=["GET", "POST"])
def build():
    session_id = g.session_id

    if not cache.has(session_id):
        flash("Session timeout", "danger")
        return redirect(url_for(".home"))

    form_id = cache.get(session_id).get("form_id")

    new_params: list[Param] = g.params.get(form_id)
    
    if request.method == "POST":
        all_params = cache.get("params")
        all_params.update({form_id: new_params})
        cache.set("params", all_params)
        write_to_params_file(new_params, form_id=form_id)

        current_app.logger.info(f"Start build with params {new_params}")

        fill_ansible_params_file(new_params)
        flash("Wait for build")
        return redirect(url_for(".wait_for_build"))

    old_params: list[Param] = cache.get("params").get(form_id)
    diff = [
        (new_param.name, new_param.defaultValue, old_param.defaultValue) 
        for new_param, old_param in zip(new_params, old_params) 
        if new_param != old_param
    ]
    
    current_app.logger.info(f"Build old_params: {old_params}\nto new_params: {new_params}")

    return render_template("main/build.html", diff=diff, form_id=form_id)


@main.route("/wait-for-build", methods=["GET", "POST"])
def wait_for_build():
    session_id = g.session_id

    if not cache.has(session_id):
        flash("Session timeout", "danger")
        return redirect(url_for(".form_choice"))
    
    if request.method == "POST":
        cache.delete(session_id)
        flash("Success", "success")
        return redirect(url_for(".home"))

    session_cache: dict[str, Any] = cache.get(session_id)
    if not get_thread_by_name(f"{session_id}_run_ansible"):
        thread = run_ansible(session_id)
        session_cache.update({"wait_thread": thread.name})
        cache.set(session_id, session_cache)
    return render_template("main/wait.html")


@main.route("/check-build", methods=["GET"])
def check_build():
    session_id = g.session_id
    if not cache.has(session_id):
        flash("Session timeout in check_build", "danger")
        return jsonify({"error": "session expired"})
    thread_name: str | None = cache.get(session_id).get("wait_thread", None)
    thread = get_thread_by_name(thread_name)
    if thread is not None:
        return jsonify({"is_alive": True})
    return jsonify({"is_alive": False})

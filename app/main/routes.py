from typing import Any
import uuid
from flask import (
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
    get_thread_by_name,
    read_params_file,
    run_ansible,
    write_to_params_file,
    Param,
)


@main.after_request
def set_session_cookie(response: Response):
    if not request.cookies.get("session_id"):
        response.set_cookie("session_id", g.session_id, samesite="None", secure=True)
    return response

@main.before_request
def load_session():
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    g.session_id = session_id


@main.before_request
def load_params():
    if cache.has(g.session_id):
        params = cache.get(g.session_id)["params"]
    elif cache.has("params"):
        params = cache.get("params")
    else:
        params = read_params_file()
        cache.set("params", params)
    g.params = params


@main.route("/", methods=["GET"])
def home():
    flash("YOOOHOOOOYOOOHOOOOYOOOHOOOOYOOOHOOOO", "info")
    return render_template("index.html")

@main.route("/fill-params", methods=["GET", "POST"])
def fill_params():
    session_id = g.session_id
    params = g.params

    if request.method == "POST":
        new_params_data = request.form
        new_params = [
            Param(name=name, defaultValue=value, description=params[i].description) 
            for i, (name, value) in enumerate(new_params_data.items())
        ]
        cache.set(session_id, {
            "params": new_params,
        })
        flash("Check params and click build", "info")
        return redirect(url_for(".build"))

    return render_template("main/fill.html", filename=params[0], params=params[1:])

@main.route("/build", methods=["GET", "POST"])
def build():
    session_id = g.session_id

    if not cache.has(session_id):
        flash("Session timeout", "danger")
        return redirect(url_for(".fill_params"))

    new_params: list[Param] = g.params
    
    if request.method == "POST":
        cache.set("params", new_params)
        write_to_params_file(new_params)
        fill_ansible_params_file(new_params)
        flash("Wait for build")
        return redirect(url_for(".wait_for_build"))

    old_params: list[Param] = cache.get("params")
    diff = [
        (new_param.name, new_param.defaultValue, old_param.defaultValue) 
        for new_param, old_param in zip(new_params, old_params) 
        if new_param != old_param
    ]
    return render_template("main/build.html", diff=diff)

@main.route("/wait-for-build", methods=["GET", "POST"])
def wait_for_build():
    session_id = g.session_id

    if not cache.has(session_id):
        flash("Session timeout", "danger")
        return redirect(url_for(".fill_params"))
    
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

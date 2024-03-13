from dataclasses import (
    dataclass,
    asdict,
)
from datetime import datetime
from functools import wraps
import json
import os
import subprocess
from threading import Thread
import threading

from flask import current_app
from flask.ctx import AppContext


@dataclass
class Param:
    name: str
    description: str
    defaultValue: str = "-"


def get_params_filename(filename: str = None) -> str:
    return filename or current_app.config.get("PARAMS_FILE")

def read_params_file(filename: str = None) -> list[Param]:
    params_filename = get_params_filename(filename)
    with open(params_filename, "r") as params_file:
        params = [Param(**param_data) for param_data in json.load(params_file)]
        return params

def write_to_params_file(data: list[Param], filename: str = None) -> None:
    params_filename = get_params_filename(filename)
    with open(params_filename, "w") as params_file:
        json.dump(
            data, params_file,
            indent=4,
            default=asdict,
        )

def fill_ansible_params_file(form_params: list[Param], ansible_params_file: str = None) -> None:
    if ansible_params_file is None:
        ansible_params_file = current_app.config.get("ANSIBLE_PARAMS_FILE")
    params = {
        param.name: param.defaultValue
        for param in form_params
    }
    with open(ansible_params_file, "w") as ansible_file:
        json.dump(
            params, ansible_file,
            indent=4,
            default=str
        )


def get_thread_by_name(thread_name: str) -> Thread:
    for thread in threading.enumerate():
        if thread.name == thread_name:
            return thread

def run_in_thread(app_context: AppContext):
    def run_func(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            app_context.push()
            return func(*args, **kwargs)
        return wrapper
    return run_func

def run_ansible_playbook(run_playbook_command, session_id, logs_dir: str = None):
    if logs_dir is None:
        logs_dir = current_app.config.get("ANSIBLE_LOG_DIR")
    log_filename = os.path.join(logs_dir, f"{datetime.now().strftime("%m.%d.%Y_%H.%M.%S")}.log")
    with open(log_filename, "w") as log_file:
        subprocess.run(run_playbook_command, stdout=log_file)


def run_ansible(session_id: str, ansible_playbook_file: str = None, ansible_params_file: str = None) -> Thread:
    if ansible_playbook_file is None:
        ansible_playbook_file = current_app.config.get("ANSIBLE_PLAYBOOK_FILE")
    if ansible_params_file is None:
        ansible_params_file = current_app.config.get("ANSIBLE_PARAMS_FILE")
    
    run_playbook_command = [
        "ansible-playbook",
        f"{ansible_playbook_file}",
        f"-vvv",
        "-e",
        f"@{ansible_params_file}",
    ]
    with open(ansible_params_file, "r") as f:
        print(f.read())

    run_ansible_in_thread = run_in_thread(current_app.app_context())(run_ansible_playbook)

    thread = Thread(name=f"{session_id}_run_ansible", target=run_ansible_in_thread, args=(run_playbook_command, session_id, ))
    thread.start()
    return thread
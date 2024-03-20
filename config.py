import os

from flask import Flask
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY")

    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME") or "admin"
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD") or "admin"
    PARAMS_DIR: str = os.getenv("FORM_PARAMS_DIR") or os.path.join(basedir, "form_params")
    ANSIBLE_PLAYBOOK_FILE: str = os.getenv("ANSIBLE_PLAYBOOK_FILE") or os.path.join(basedir, "ansible", "playbook.yml")
    ANSIBLE_PARAMS_FILE: str = os.getenv("ANSIBLE_PARAMS_FILE") or os.path.join(basedir, "ansible", "params.json")
    ANSIBLE_LOG_DIR: str = os.getenv("ANSIBLE_LOG_DIR") or os.path.join(basedir, "ansible", "logs")
    
    CACHE_TYPE: str = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT: int = 300

    @classmethod
    def init_app(cls, app: Flask) -> None:
        if not os.path.exists(cls.PARAMS_DIR):
            os.mkdir(cls.PARAMS_DIR)
        if not os.path.exists(cls.ANSIBLE_LOG_DIR):
            os.mkdir(cls.ANSIBLE_LOG_DIR)


class DevConfig(Config):
    DEBUG: bool = True

    @classmethod
    def init_app(cls, app: Flask) -> None:
        super().init_app(app)
        app.debug = cls.DEBUG


class ProdConfig(Config):
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD")

    @classmethod
    def init_app(cls, app: Flask):
        super().init_app(app)
    
        import logging
        from logging import StreamHandler

        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
    'development': DevConfig,
    'production': ProdConfig,

    'default': DevConfig
}

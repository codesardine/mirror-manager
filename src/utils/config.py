import secrets
import os

settings = {
    "SECRET_KEY": secrets.token_hex(32),
    "SQLALCHEMY_DATABASE_URI": 'sqlite:///db.sqlite',
    "SECURITY_PASSWORD_SALT": secrets.token_hex(32),
    "MAIL_DEFAULT_SENDER": os.environ.get("MAIL_DEFAULT_SENDER"),
    "MAIL_SERVER": os.environ.get("MAIL_SERVER"),
    "MAIL_PORT": os.environ.get("MAIL_PORT"),
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_DEBUG": False,
    "MAIL_USERNAME": os.environ.get("MAIL_USERNAME"),
    "MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD"),
    "CHECK_BRANCHES_TIMEOUT_MINUTES": 10,
    "CHECK_OFFLINE_MIRRORS_HOURS": 1,
    "MASTER_RSYNC": "repo.nix.dk/manjaro/",
    "BRANCHES": ("stable", "testing", "unstable")
}

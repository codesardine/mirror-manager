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
    "WHITELIST_EMAIL": os.environ.get("WHITELIST_EMAIL"),
    "CHECK_BRANCHES_MINUTES": 30,
    "CHECK_OFFLINE_MIRRORS_HOURS": 24,
    "CHECK_UNSYNC_MIRRORS_HOURS": 1,
    "WEEKLY_EMAILS": 1,
    "MASTER_RSYNC": "repo.manjaro.org/repo/",
    "BRANCHES": ("stable", "testing", "unstable", "arm-stable", "arm-testing", "arm-unstable"),
    "USER_AGENT": "ManjaroMirrorBot/1.1"
}

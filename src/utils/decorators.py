from flask import flash, redirect, url_for
from flask_login import current_user
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def check_is_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_confirmed:
            flash("Please confirm your account!", "warning")
            return redirect(url_for("account.user_account"))
        return func(*args, **kwargs)

    return decorated_function
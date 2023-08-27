from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from werkzeug.security import check_password_hash
from src.account.models import Account
from src.utils.extensions import db
from flask_login import login_user, login_required, logout_user
from src.account.token import generate_token
from src.utils.email import send_email
from src.auth.utils import is_safe_url
from werkzeug.security import generate_password_hash
from datetime import datetime

auth = Blueprint("auth", __name__)

@auth.route("/login")
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    recover = True if request.form.get('recover') else False
    account = Account.query.filter_by(email=email).first()

    if recover:
        if email:
            token = account.get_reset_token()
            html = render_template("email/recover-password.html", token=token, url=request.host_url)
            subject = "Password Recover"

            try:
                send_email(account.email, subject, html)
                flash("A confirmation email has been sent via email.")
                return redirect(url_for("main.index"))
            except Exception as e:
                print(e)
                flash("Enable to send recovery email.", "warning")
                return redirect(url_for('auth.login')) 
        else:
            flash("Please insert your email address.", "warning")
            return redirect(url_for('auth.login'))

    else:
        if not account or not check_password_hash(account.password, password):
            flash('Please check your login details and try again.', "warning")        
            return redirect(url_for('auth.login')) 

        login_user(account, remember=remember)
        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)

        return redirect(next or url_for('mirror.my_mirrors'))

@auth.route("/signup")
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')

    if Account.query.filter_by(email=email).first():
        flash('Email address already exists', "warning")
        return redirect(url_for('auth.login'))

    if not email:
        flash('Please insert a email address.', "warning")
        return redirect(url_for('auth.signup', email=email))

    if not name:
        flash('Please insert your name.', "warning")
        return redirect(url_for('auth.signup'))

    if not password:
        flash('Please insert a password.', "error")
        return redirect(url_for('auth.signup'))  
    elif password != password_confirm:
        flash('Your password does not match.', "warning")
        return redirect(url_for('auth.signup')) 
    
    account = Account()
    account.email = email
    account.name = name
    account.password = generate_password_hash(password)
    account.created_on = datetime.now()
    account.is_admin = False
    account.is_confirmed = False
    account.confirmed_on = None
    token = generate_token(account.email)
    confirm_url = url_for("account.confirm_email", token=token, _external=True)
    html = render_template("email/confirm_email.html", confirm_url=confirm_url)
    subject = "Please confirm your email"

    try:
        send_email(account.email, subject, html)
        account.save()
        login_user(account)
        flash("A confirmation email has been sent via email.")
        return redirect(url_for("account.user_account"))
    except Exception:
        flash("Enable to send confirmation email.", "warning")
        return redirect(url_for('auth.signup')) 

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
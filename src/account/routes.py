from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user
from src.utils.extensions import db
from src.account.models import Account
from datetime import datetime
from src.account.token import confirm_token, generate_token
from src.utils import email
from .token import verify_reset_token
from werkzeug.security import generate_password_hash


account = Blueprint("account", __name__)

@account.route('/account')
@login_required
def user_account():
    return render_template('account.html', account=current_user)

@account.route('/account', methods=['POST'])
@login_required
def account_post():
    account_id = request.form.get('account_id')
    delete_account = request.form.get('delete-account')
    if delete_account:
        acc = Account.query.get(account_id)
        acc.delete()
        flash(f'Account Deleted, good bye.')
        return redirect(url_for('main.index'))

@account.route("/confirm/<token>")
@login_required
def confirm_email(token):
    if current_user.is_confirmed:
        flash("Account already confirmed.", "success")
        return redirect(url_for("mirror.my_mirrors"))
    email = confirm_token(token)
    user = Account.query.filter_by(email=current_user.email).first_or_404()
    if user.email == email:
        user.is_confirmed = True
        user.confirmed_on = datetime.now()
        user.save()
        flash("You have confirmed your account. Thanks!")
        return redirect(url_for("mirror.my_mirrors"))
    else:
        flash("The confirmation link is invalid or has expired.", "error")
    return redirect(url_for("account.user_account"))

@account.route("/password-reset/<token>", methods=['GET'])
def reset_password(token):
    user = verify_reset_token(token)
    if user:
        return render_template("password_reset.html", token=token)
    return redirect(url_for("auth.login"))

@account.route("/password-reset/<token>", methods=['POST'])
def reset_password_post(token):
    user = verify_reset_token(token)    
    new_password = request.form.get('new_password')
    password_confirm = request.form.get('confirm_password')
    if new_password and password_confirm  and new_password == password_confirm and " " not in new_password:
        user.password = generate_password_hash(new_password)
        user.save()
        flash("Your new password was saved")
    else:
        flash("Your password fields do not match or have empty spaces", "warning")
        return render_template("password_reset.html", token=token)
    
    return redirect(url_for("auth.login"))

@account.route("/resend")
@login_required
def resend_confirmation():
    if not current_user.is_confirmed:        
        token = generate_token(current_user.email)
        confirm_url = url_for("account.confirm_email", token=token, _external=True)
        html = render_template("confirm_email.html", confirm_url=confirm_url)
        subject = "Please confirm your email"
        email.send_email(current_user.email, subject, html)
        flash("A new confirmation email has been sent.")
        return redirect(url_for("account.user_account"))
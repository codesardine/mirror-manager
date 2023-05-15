from flask import Blueprint, render_template
from .mirrors.models import Mirror

main = Blueprint("main", __name__)

@main.route("/")
def index():
    mirrors = Mirror().query.all()
    return render_template('index.html', mirrors=mirrors)

from flask import Blueprint, render_template
from .mirrors.models import Mirror

main = Blueprint("main", __name__)

@main.route("/")
def index():
    mirrors = Mirror().query.filter_by(active=True, in_sync=True).order_by(Mirror.country).all()
    return render_template(
        'index.html',
        mirrors=mirrors,
        total=len(mirrors)
        )

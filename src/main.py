from flask import Blueprint, render_template, request
from .mirrors.models import Mirror

main = Blueprint("main", __name__)

@main.route("/" , methods=['GET', 'POST'])
def index():
    mirrors = Mirror().query.filter_by(active=True).order_by(Mirror.country).all()
    select = request.form.get('arch-select')

    return render_template(
        'index.html',
        mirrors=mirrors,
        total=len(mirrors),
        select=select
        )


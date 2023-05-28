from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail 
from .utils.config import settings
from .utils.extensions import db
from .account.models import Account
from apscheduler.triggers.interval import IntervalTrigger
from .utils.decorators import scheduler
from .mirrors.utils import validate_branches, check_offline_mirrors, populate_master_state
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config.update(settings)  

migrate = Migrate(app, db)
mail = Mail(app)
mail.init_app(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

csrf = CSRFProtect()
csrf.init_app(app)

from .auth.routes import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from .main import main as main_blueprint
app.register_blueprint(main_blueprint)

from .mirrors.routes import mirror as mirror_blueprint
app.register_blueprint(mirror_blueprint)

from .account.routes import account as account_blueprint
app.register_blueprint(account_blueprint)

@login_manager.user_loader
def load_user(user_id):
    return Account.query.get(int(user_id))

@scheduler.scheduled_job(IntervalTrigger(
        minutes=settings["CHECK_BRANCHES_TIMEOUT_MINUTES"]))
def check_branches():
    with app.app_context():
        populate_master_state()
        validate_branches()

@scheduler.scheduled_job(IntervalTrigger(
        hours=settings["CHECK_OFFLINE_MIRRORS_HOURS"]))
def check_down_state():
    with app.app_context():
        check_offline_mirrors()

scheduler.start()

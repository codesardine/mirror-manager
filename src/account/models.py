from flask_login import UserMixin
from ..utils.extensions import db
from werkzeug.security import generate_password_hash
from datetime import datetime


class Account(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    mirror = db.relationship('Mirror', backref='account', cascade="all, delete")

    def __init__(
        self, email, name, password, is_admin=False, is_confirmed=False, confirmed_on=None
    ):
        self.email = email
        self.name = name
        self.password = generate_password_hash(password)
        self.created_on = datetime.now()
        self.is_admin = is_admin
        self.is_confirmed = is_confirmed
        self.confirmed_on = confirmed_on


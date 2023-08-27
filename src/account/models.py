from flask_login import UserMixin
from src.utils.extensions import db
from src.models import DbMixin
import jwt
import datetime
from datetime import timedelta
from ..utils.config import settings

class Account(UserMixin, DbMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    mirror = db.relationship('Mirror', backref='account', cascade="all, delete") 

    def get_reset_token(self):
        delta = timedelta(hours=1)
        now = datetime.datetime.now().astimezone()
        expires = now + delta
        return jwt.encode(
            {
            "exp": expires.timestamp(), 
            "nbf": now,
            "sub": "Password reset",
            "email": self.email,
            },
        key=settings["SECRET_KEY"],
        algorithm="HS256",
    )

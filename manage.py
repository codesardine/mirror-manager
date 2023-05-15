#!/usr/bin/python3
from src import db, app
import sys

def create_db():
    with app.app_context():
        db.create_all()

def delete_db():
    with app.app_context():
        db.drop_all()
        
if "create-db" in sys.argv:
    create_db()

if "delete-db" in sys.argv:
    delete_db()

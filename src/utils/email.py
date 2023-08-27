
from flask_mail import Message
from .config import settings
from src import mail
from threading import Thread
from src import app

def send_email_task(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=settings["MAIL_DEFAULT_SENDER"],
    )

    Thread(target=send_email_task, args=(app, msg)).start()
    
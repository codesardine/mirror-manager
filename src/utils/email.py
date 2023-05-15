
from flask_mail import Message
from .config import settings
from src import mail


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=settings["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)
    
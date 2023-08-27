from itsdangerous import URLSafeTimedSerializer
from ..utils.config import settings
import jwt
from .models import Account

def generate_token(email):
    serializer = URLSafeTimedSerializer(settings["SECRET_KEY"])
    return serializer.dumps(email, salt=settings["SECURITY_PASSWORD_SALT"])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(settings["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=settings["SECURITY_PASSWORD_SALT"], max_age=expiration
        )
        return email
    except Exception:
        return False
    
def verify_reset_token(token):
        try:
            decode = jwt.decode(
                 token,
                 settings["SECRET_KEY"],
                 algorithms=["HS256"])
        except Exception as e:
            print(e)
            return
        return Account.query.filter_by(email=decode["email"]).first_or_404()

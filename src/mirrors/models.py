from ..utils.extensions import db


class MasterRepo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    master_hash = db.Column(db.String(100))
    master_last_sync = db.Column(db.String(100))

    stable_hash = db.Column(db.String(100), nullable=True)
    stable_last_sync = db.Column(db.String(100), nullable=True)

    testing_hash = db.Column(db.String(100), nullable=True)
    testing_last_sync = db.Column(db.String(100), nullable=True)

    unstable_hash = db.Column(db.String(100), nullable=True)
    unstable_last_sync = db.Column(db.String(100), nullable=True)

    arm_stable_hash = db.Column(db.String(100), nullable=True)
    arm_stable_last_sync = db.Column(db.String(100), nullable=True)

    arm_testing_hash = db.Column(db.String(100), nullable=True)
    arm_testing_last_sync = db.Column(db.String(100), nullable=True)

    arm_unstable_hash = db.Column(db.String(100), nullable=True)
    arm_unstable_last_sync = db.Column(db.String(100), nullable=True)


class Mirror(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    address = db.Column(db.String(100), unique=True, nullable=False)
    rsync = db.Column(db.Boolean)
    country = db.Column(db.String(25), nullable=False)
    http = db.Column(db.Boolean)
    https = db.Column(db.Boolean)
    speed = db.Column(db.String(10))
    in_sync = db.Column(db.Boolean, default=True)

    last_sync = db.Column(db.String(100))
    active = db.Column(db.Boolean)
    user_notified = db.Column(db.Boolean)   
    ip_whitelist = db.Column(db.String())

    stable_hash = db.Column(db.String(100))
    stable_last_sync = db.Column(db.String(100))
    stable_is_sync = db.Column(db.Boolean)

    testing_hash = db.Column(db.String(100))
    testing_last_sync = db.Column(db.String(100))
    testing_is_sync = db.Column(db.Boolean)

    unstable_hash = db.Column(db.String(100))
    unstable_last_sync = db.Column(db.String(100))
    unstable_is_sync = db.Column(db.Boolean)

    arm_stable_hash = db.Column(db.String(100))
    arm_stable_last_sync = db.Column(db.String(100))
    arm_stable_is_sync = db.Column(db.Boolean)

    arm_testing_hash = db.Column(db.String(100))
    arm_testing_last_sync = db.Column(db.String(100))
    arm_testing_is_sync = db.Column(db.Boolean)

    arm_unstable_hash = db.Column(db.String(100))
    arm_unstable_last_sync = db.Column(db.String(100))
    arm_unstable_is_sync = db.Column(db.Boolean)



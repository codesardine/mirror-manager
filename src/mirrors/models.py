from src.utils.extensions import db
from src.utils.config import settings


class ModelBase():
    id = db.Column(db.Integer, primary_key=True) 
    last_modified = db.Column(db.DateTime, nullable=True)
    hash = db.Column(db.String(100))
    last_sync = db.Column(db.String(100))

    def last_sync_date(self):
        from datetime import datetime
        if self.last_sync != None:
            remove_time = self.last_sync.split(" ")[0]
            return datetime.strptime(remove_time, '%Y-%m-%d').date()
        return 999

    def save(self):
        db.session.add(self)
        db.session.commit()


class MasterRepo(db.Model, ModelBase):   
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


class Mirror(db.Model, ModelBase):
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    address = db.Column(db.String(100), unique=True, nullable=False)
    rsync = db.Column(db.Boolean)
    country = db.Column(db.String(25), nullable=False)
    http = db.Column(db.Boolean)
    https = db.Column(db.Boolean)
    speed = db.Column(db.String(10))
    points = db.Column(db.Integer, default=settings["MAX_POINTS"])
  
    active = db.Column(db.Boolean)
    user_notified = db.Column(db.Boolean)   
    ip_whitelist = db.Column(db.String())

    stable_hash = db.Column(db.String(100))
    stable_last_sync = db.Column(db.String(100))

    testing_hash = db.Column(db.String(100))
    testing_last_sync = db.Column(db.String(100))

    unstable_hash = db.Column(db.String(100))
    unstable_last_sync = db.Column(db.String(100))

    arm_stable_hash = db.Column(db.String(100))
    arm_stable_last_sync = db.Column(db.String(100))

    arm_testing_hash = db.Column(db.String(100))
    arm_testing_last_sync = db.Column(db.String(100))

    arm_unstable_hash = db.Column(db.String(100))
    arm_unstable_last_sync = db.Column(db.String(100))

    def get_points(self):
        return f"{int(self.points/settings['MAX_POINTS']*100)}%"

    def stable_in_sync(self):
        master = MasterRepo().query.get(1)
        if self.stable_hash != master.stable_hash:
            return False
        return True

    def testing_in_sync(self):
        master = MasterRepo().query.get(1)
        if self.testing_hash != master.testing_hash:
            return False
        return True

    def unstable_in_sync(self):
        master = MasterRepo().query.get(1)
        if self.unstable_hash != master.unstable_hash:
            return False
        return True

    def arm_stable_in_sync(self):
        master = MasterRepo().query.get(1)
        if self.arm_stable_hash != master.arm_stable_hash:
            return False
        return True

    def arm_testing_in_sync(self):
        master = MasterRepo().query.get(1)
        if self.arm_testing_hash != master.arm_testing_hash:
            return False
        return True

    def arm_unstable_in_sync(self):
        master = MasterRepo().query.get(1)
        if self.arm_unstable_hash != master.arm_unstable_hash:
            return False
        return True
    
    def is_out_sync(self):
        master = MasterRepo().query.get(1)
        if self.arm_unstable_hash != master.arm_unstable_hash and \
            self.arm_testing_hash != master.arm_testing_hash and \
            self.arm_stable_hash != master.arm_stable_hash and \
            self.unstable_hash != master.unstable_hash and \
            self.testing_hash != master.testing_hash and \
            self.stable_hash != master.stable_hash:
            return True
        return False
    
    def is_outdated_by(self):
        date = self.last_sync_date()
        if date == 999:
            return 999
        master = MasterRepo().query.get(1)
        delta = master.last_sync_date() - date
        return delta.days
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()

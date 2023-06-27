from ..utils.extensions import db
  

class MasterRepo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    hash = db.Column(db.String(100))
    last_sync = db.Column(db.String(100))

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
    hash = db.Column(db.String(100))

    last_sync = db.Column(db.String(100))
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

    def is_in_sync(self):
        master = MasterRepo().query.get(1)
        if self.arm_unstable_hash != master.arm_unstable_hash or \
            self.arm_testing_hash != master.arm_testing_hash or \
            self.arm_stable_hash != master.arm_stable_hash or \
            self.unstable_hash != master.unstable_hash or \
            self.testing_hash != master.testing_hash or \
            self.stable_hash != master.stable_hash:
            return False
        return True

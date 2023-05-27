import requests, time
from requests.exceptions import HTTPError
from ..mirrors.models import Mirror, MasterRepo
from datetime import datetime 
from ..utils.extensions import db
from ..utils.config import settings
import concurrent.futures


def state_check(protocol, address, branch=None):    
    if branch:
        file = f"{branch}/state"
    else:
        file = "state"
    
    start = time.time()

    try:
        headers = {
            "User-Agent": "Manjaro Mirror Manager/1.0"
        }
        response = requests.get(f'{protocol}://{address}/{file}', headers=headers, timeout=3, stream=True)
        response.raise_for_status()
        end = time.time()
        elapsed = end - start
        ip = response.raw._connection.sock.getpeername()
    except HTTPError:
        return {"state_file_exists": False}
    except Exception: 
        return {"state_file_exists": False}
    
    return {
        "state_file_exists": True,
        "access_time": str(elapsed)[:5],
        "state_file": response.text,
        "ip": ip[0]
        }
    
def get_state_contents(file):
    sync = {}
    for line in file.splitlines():
        if line.startswith("state="):
            hash = line.split("state=")[1]
            sync["hash"] = hash
        if line.startswith("date="):
            datetime_str = line.split("date=")[1].replace("Z", "")
            iso_format = datetime.fromisoformat(datetime_str)
            date = '{:%Y-%m-%d %H:%M}'.format(iso_format)
            sync["last_sync"] = date
    return sync

def validate_state(mirror, address, protocol, master=False, branch=None):
    if branch:
        server = state_check(protocol, address=address, branch=branch)
    else:
        server = state_check(protocol, address=address)
        
    if server["state_file_exists"]:
        state_file = get_state_contents(server["state_file"])
        if not branch:
            mirror.last_sync = state_file["last_sync"]
        else:
            if not master:
                mirror.speed = server["access_time"]
                mirror.http = True
                master_mirror = MasterRepo().query.first()

            def set_status(mirror_hash, master_hash, is_in_sync):
                if mirror_hash != master_hash:
                    is_in_sync = False
                else:
                    is_in_sync = True
            
            if branch == "stable":
                mirror.stable_hash = state_file["hash"].strip()
                mirror.stable_last_sync = state_file["last_sync"]
                if not master:
                    set_status(
                        mirror.stable_hash,
                        master_mirror.stable_hash,
                        mirror.stable_is_sync
                        )            

            elif branch == "testing":
                mirror.testing_hash = state_file["hash"].strip()
                mirror.testing_last_sync = state_file["last_sync"]
                if not master:set_status(
                        mirror.testing_hash,
                        master_mirror.testing_hash,
                        mirror.testing_is_sync
                        ) 

            elif branch == "unstable":
                mirror.unstable_hash = state_file["hash"].strip()
                mirror.unstable_last_sync = state_file["last_sync"]
                if not master:
                    set_status(
                        mirror.unstable_hash,
                        master_mirror.unstable_hash,
                        mirror.unstable_is_sync
                        ) 
    else:
        if not master:
            if "https" in protocol:
                mirror.https = False
            else:
                mirror.http = False
    
    db.session.add(mirror)      
    db.session.commit()

def validate_branches():
    branches = settings["BRANCHES"]
    mirrors = Mirror().query.filter_by(active=True).all()
    futures = []
    with concurrent.futures.ThreadPoolExecutor(60) as executor:
        for mirror in mirrors:
            protocols = ("http", "https")
            for protocol in protocols:
                futures.append(executor.submit(
                        validate_state(mirror, mirror.address, protocol)
                        ))
                
            for branch in branches:
                if mirror.https:
                    futures.append(executor.submit(
                            validate_state(mirror, mirror.address, "https", branch=branch)
                            ))
                elif mirror.http:
                    futures.append(executor.submit(
                            validate_state(mirror, mirror.address, "http", branch=branch)
                            ))

        for mirror in mirrors:
            if not mirror.user_notified and not mirror.http and not mirror.https:
                from ..utils.email import send_email
                from ..account.models import Account
                user = Account().query.filter_by(id=mirror.account_id)
                mirror.active = False
                send_email(
                    user.email,
                    "Issues found with your manjaro mirror",
                    f"Your Manjaro mirror {mirror.address} has been deactivated, fix any issues with your server and Mirror Manager will reactivate your mirror."
                    )
                mirror.user_notified = True
                db.session.add(mirror)        
        db.session.commit()

def check_offline_mirrors():
    mirrors = Mirror().query.filter_by(active=False).all()
    for mirror in mirrors:
        protocols = {
            "http": False,
            "https": False
        }
        
        for protocol in protocols:
            server = state_check(protocol, mirror.address)
            if server["state_file_exists"]:
                protocols[protocol] = server["state_file_exists"]
                mirror.speed = server["access_time"]
                mirror.user_notified = False
                mirror.active = True
            
                if "https" in protocol:
                    mirror.https = True
                elif "http" in protocol:
                    mirror.http = True
                    
        if mirror.active:
            from ..utils.email import send_email
            from ..account.models import Account
            user = Account().query.filter_by(id=mirror.account_id)
            send_email(
                user.email,
                "Your mirror is back online",
                f"Your Manjaro mirror {mirror.address}, has been activated."
                )
            db.session.add(mirror)        
    
    db.session.commit()

def populate_master_state():
    branches = settings["BRANCHES"]
    repo = settings["MASTER_RSYNC"]
    master_mirror = MasterRepo().query.first()
    if not master_mirror:
        master_mirror = MasterRepo()

    protocol = "https"
    server = state_check(protocol, address=repo)
    file = get_state_contents(server["state_file"])
    master_mirror.master_hash = file["hash"]
    master_mirror.master_last_sync = file["last_sync"]
    db.session.add(master_mirror)  
    db.session.commit()    

    for branch in branches:
       validate_state(master_mirror, repo, protocol, branch=branch, master=True)    
    
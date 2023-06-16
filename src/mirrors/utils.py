import requests, time
from requests.exceptions import HTTPError
from src.mirrors.models import Mirror, MasterRepo
from datetime import datetime, date, timedelta
from src.utils.extensions import db
from src.utils.config import settings
import concurrent.futures
import socket

def whitelist_email():
    from src.utils.email import send_email
    query = Mirror().query.filter_by(active=True).all()  
    mirror_list = []  
    for mirror in query:
        mirror_list.append(mirror.ip_whitelist)

    mirrors = '<br />'.join(mirror_list)
    
    send_email(
        settings["WHITELIST_EMAIL"],
        "Mirrors to whitelist",
        f"""A new weekly IP list is available.
        <br />
        <br />
        {mirrors}"""
        )

def validate_ownership(protocol, address, file):        
    target = f"{protocol}://{address}{file}"

    try:
        headers = {
            "User-Agent": settings["USER_AGENT"]
        }
        response = requests.get(f'{target}', headers=headers, timeout=3, stream=True)
        response.raise_for_status()
    except HTTPError:
        return False
    except Exception: 
        return False
    
    return True

def state_check(protocol, address, branch=None):    
    if branch:
        file = f"{branch}/state"
    else:
        file = "state"
    
    start = time.time()
    target = f"{protocol}://{address}{file}"

    try:
        headers = {
            "User-Agent": settings["USER_AGENT"]
        }
        response = requests.get(f'{target}', headers=headers, timeout=3, stream=True)
        response.raise_for_status()
        end = time.time()
        elapsed = end - start
        res = response.raw._connection.sock.getpeername()
        ip = res[0]
        #port = res[1]
        try:
            ipv6 = socket.getaddrinfo(address, None, family=socket.AF_INET6)
            ip += f" {ipv6[0][4][0]}"
        except Exception as e:
            print(e)
    except HTTPError:
        return {"state_file_exists": False}
    except Exception: 
        return {"state_file_exists": False}
    
    return {
        "state_file_exists": True,
        "access_time": str(elapsed)[:5],
        "state_file": response.text,
        "ip": ip
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
            if protocol == "http":
                mirror.http = True
            elif protocol == "https:":
                mirror.https = True
        else:
            if not master:
                mirror.speed = server["access_time"]
                master_mirror = MasterRepo().query.first()
            
            if branch == "stable":
                mirror.stable_hash = state_file["hash"].strip()
                mirror.stable_last_sync = state_file["last_sync"]
                if not master:
                    if mirror.stable_hash != master_mirror.stable_hash:
                        mirror.stable_is_sync = False
                    else:
                        mirror.stable_is_sync = True

            elif branch == "testing":
                mirror.testing_hash = state_file["hash"].strip()
                mirror.testing_last_sync = state_file["last_sync"]
                if not master:
                    if mirror.testing_hash != master_mirror.testing_hash:
                        mirror.testing_is_sync = False
                    else:
                        mirror.testing_is_sync = True

            elif branch == "unstable":
                mirror.unstable_hash = state_file["hash"].strip()
                mirror.unstable_last_sync = state_file["last_sync"]
                if not master:
                    if mirror.unstable_hash != master_mirror.unstable_hash:
                        mirror.unstable_is_sync = False
                    else:
                        mirror.unstable_is_sync = True

            elif branch == "arm-stable":
                mirror.arm_stable_hash = state_file["hash"].strip()
                mirror.arm_stable_last_sync = state_file["last_sync"]
                if not master:
                    if mirror.arm_stable_hash != master_mirror.arm_stable_hash:
                        mirror.arm_stable_is_sync = False
                    else:
                        mirror.arm_stable_is_sync = True

            elif branch == "arm-testing":
                mirror.arm_testing_hash = state_file["hash"].strip()
                mirror.arm_testing_last_sync = state_file["last_sync"]
                if not master:
                    if mirror.arm_testing_hash != master_mirror.arm_testing_hash:
                        mirror.arm_testing_is_sync = False
                    else:
                        mirror.arm_testing_is_sync = True

            elif branch == "arm-unstable":
                mirror.arm_unstable_hash = state_file["hash"].strip()
                mirror.arm_unstable_last_sync = state_file["last_sync"]
                if not master:
                    if mirror.arm_unstable_hash != master_mirror.arm_unstable_hash:
                        mirror.arm_unstable_is_sync = False
                    else:
                        mirror.arm_unstable_is_sync = True
    else:
        if not master and not branch:
            if "https" in protocol:
                mirror.https = False
            else:
                mirror.http = False
            
            if not mirror.http and not mirror.https:
                mirror.active = False
    
    db.session.add(mirror)      
    db.session.commit()

def validate_branches():
    branches = settings["BRANCHES"]
    mirrors = Mirror().query.filter_by(active=True, in_sync=True).all()
    futures = []
    with concurrent.futures.ThreadPoolExecutor(60) as executor:
        for mirror in mirrors:
            if mirror.https:
                futures.append(executor.submit(
                        validate_state(mirror, mirror.address, "https")
                        ))
            elif mirror.http:
                futures.append(executor.submit(
                        validate_state(mirror, mirror.address, "http")
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
                from src.utils.email import send_email
                from src.account.models import Account
                user = Account.query.get(mirror.account_id)
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
    mirrors = Mirror().query.filter_by(active=False, in_sync=True).all()
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
            from src.utils.email import send_email
            from src.account.models import Account
            user = Account.query.get(mirror.account_id)
            send_email(
                user.email,
                "Your mirror is back online",
                f"Your Manjaro mirror {mirror.address}, has been activated."
                )
            db.session.add(mirror)        
    
    db.session.commit()

def check_unsync_mirrors():
    mirrors = Mirror().query.filter_by(active=True).all()
    for mirror in mirrors:
        branches = (
            mirror.stable_is_sync, 
            mirror.testing_is_sync, 
            mirror.unstable_is_sync,
            mirror.arm_stable_is_sync,
            mirror.arm_testing_is_sync,
            mirror.arm_unstable_is_sync
            )

        today = date.today()
        m_date = mirror.last_sync.split(" ")[0]
        last_sync = datetime.strptime(m_date, '%Y-%m-%d').date()
        one_day = today - timedelta(days=1)
        seven_days = today - timedelta(days=7)

        if not any(branches) and last_sync < seven_days:
            db.session.delete(mirror)
            db.session.commit()
            send_email(
                user.email,
                "Mirror out of sync for a week",
                f"Your Manjaro mirror {mirror.address}, is outdated for a week and is now deleted."
                )
               
        elif not any(branches) and last_sync < one_day:
            from src.utils.email import send_email
            from src.account.models import Account
            user = Account.query.get(mirror.account_id)
            mirror.in_sync = False
            send_email(
                user.email,
                "Your mirror is out of sync",
                f"Your Manjaro mirror {mirror.address}, is outdated for 24h, there might be an issue with your sync process."
                )
        else:
            mirror.in_sync = True

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
    
def remove_unused_accounts():
    from src.utils.email import send_email
    from src.account.models import Account
    accounts = Account.query.all()
    for account in accounts:
        mirrors = Mirror().query.filter_by(account_id=account.id).first()
        today = date.today()
        created_on = account.created_on.date()
        defined_days = today - timedelta(days=1)

        if mirrors == None and created_on < defined_days:
            db.session.delete(account)
            db.session.commit()
            send_email(
                account.email,
                "Your account has been deleted",
                f"Your Manjaro mirror manager account, was unused and has been deleted."
                )
            
def test_rsync(address):
    import subprocess
    cmd = ["rsync", f"rsync://{address}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        result = proc.returncode
        if result == 0:
            return True  
    except subprocess.TimeoutExpired:
        pass

    return False

def test_country(country):
    import pycountry
    from flask import redirect, url_for, flash
    if not "global" in country:
        try:
            is_country = pycountry.countries.get(name=country)
            if not is_country:
                fuzzy_search = pycountry.countries.search_fuzzy(country)
                new_country = fuzzy_search[0].name

                if new_country and "," in new_country:
                    country = new_country.split(",")[0]
                elif new_country and "," not in new_country:
                    country = new_country
                else:
                    flash(f'Invalid country {country}', "error")
                    return redirect(url_for('mirror.my_mirrors'))
        except:
            flash(f'Invalid country {country}', "error")
            return redirect(url_for('mirror.my_mirrors'))   
    else:
        country = "global"

    return country.lower()

def sanitize_url(url):
    if not url.endswith("/"):
        url = url + "/"

    if "http" in url:
        url = url.split("://")[1]

    return url.strip().replace(" ", "")
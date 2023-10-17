import requests, time
from requests.exceptions import HTTPError
from src.mirrors.models import Mirror, MasterRepo
from datetime import datetime, date, timedelta
from src.utils.config import settings
import concurrent.futures
import socket
from dateutil.parser import parse as parsedate

def get_state_path(branch=None):
    if branch != None:
        return f"{branch}/state"  
    else:
        return "state"

def headers():
    return {
            "User-Agent": settings["USER_AGENT"],
            #'Accept-encoding': 'gzip',
        }

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
        response = requests.get(f'{target}', headers=headers(), timeout=3, stream=True)
        response.raise_for_status()
    except HTTPError:
        return False
    except Exception: 
        return False
    
    return True

def get_ip(address):  
        url = address.split("/")[0]
        ip = socket.getaddrinfo(url, None)
        ipv4 = ip[0][4][0]
        print(ipv4)
        try:
            ipv6 = ip[3][4][0]
            print(ipv6)
            return f"{ipv4} {ipv6}"
        except IndexError:
            return ipv4

def state_check(protocol, address, branch=None):             
    start = time.time()
    target = f"{protocol}://{address}{get_state_path(branch)}"

    try:
        response = requests.get(f'{target}', headers=headers(), timeout=3, stream=True)
        response.raise_for_status()
        end = time.time()
        elapsed = end - start
        
    except HTTPError:
        return {"state_file_exists": False}
    except Exception: 
        return {"state_file_exists": False}
    
    json = {
        "state_file_exists": True,
        "state_file": response.text,
        }
    
    if not branch:
        json["ip"] = get_ip(address)
        json["access_time"] = str(elapsed)[:5]
    
    return json
    
def get_state_contents(file):
    sync = {}
    for line in file.splitlines():
        if line.startswith("state="):
            hash = line.split("state=")[1]
            sync["hash"] = hash.strip()
        if line.startswith("date="):
            datetime_str = line.split("date=")[1].replace("Z", "")
            iso_format = datetime.fromisoformat(datetime_str)
            date = '{:%Y-%m-%d %H:%M}'.format(iso_format)
            sync["last_sync"] = date
    return sync

def validate_state(mirror, address, protocol, master=False, branch=None):
        server = state_check(protocol, address=address, branch=branch)
            
        if server["state_file_exists"]:
            state_file = get_state_contents(server["state_file"])
            if not branch:
                mirror.last_sync = state_file["last_sync"]
                mirror.hash = state_file["hash"].strip()
                mirror.speed = server["access_time"]
            else:                
                if branch == "stable":
                    mirror.stable_hash = state_file["hash"]
                    mirror.stable_last_sync = state_file["last_sync"]                        

                elif branch == "testing":
                    mirror.testing_hash = state_file["hash"]
                    mirror.testing_last_sync = state_file["last_sync"]

                elif branch == "unstable":
                    mirror.unstable_hash = state_file["hash"]
                    mirror.unstable_last_sync = state_file["last_sync"]

                elif branch == "arm-stable":
                    mirror.arm_stable_hash = state_file["hash"]
                    mirror.arm_stable_last_sync = state_file["last_sync"]

                elif branch == "arm-testing":
                    mirror.arm_testing_hash = state_file["hash"]
                    mirror.arm_testing_last_sync = state_file["last_sync"]

                elif branch == "arm-unstable":
                    mirror.arm_unstable_hash = state_file["hash"]
                    mirror.arm_unstable_last_sync = state_file["last_sync"]

            mirror.save()

        else:
            if not master and not branch:                
                if not mirror.http and not mirror.https:
                    mirror.active = False
                    mirror.save()
        
def validate_branches():
    branches = settings["BRANCHES"]
    mirrors = Mirror().query.filter_by(active=True).all()
    master = MasterRepo().query.get(1)
    futures = []
    with concurrent.futures.ThreadPoolExecutor(20) as executor:
        start = time.time()
        for mirror in mirrors:
            print()
            print(mirror.address, mirror.get_protocol())
            if mirror.hash != master.hash:
                def queue(mirror, branch=None):
                    if branch:
                        print(f"Updating", branch, mirror.hash, master.hash)
                        return validate_state(mirror, mirror.address, mirror.get_protocol(), branch=branch)
                    else:
                        print("Updating", "Hash", mirror.hash, master.hash)
                        return validate_state(mirror, mirror.address, mirror.get_protocol())
                
                futures.append(executor.submit(queue(mirror)))                  
                for branch in branches:
                    if branch == "stable" and mirror.stable_hash != master.stable_hash:
                        futures.append(executor.submit(queue(mirror, branch)))

                    elif branch == "testing" and mirror.testing_hash != master.testing_hash:
                        futures.append(executor.submit(queue(mirror, branch)))

                    elif branch == "unstable" and mirror.unstable_hash != master.unstable_hash:
                        futures.append(executor.submit(queue(mirror, branch)))

                    elif branch == "arm-stable" and mirror.arm_stable_hash != master.arm_stable_hash:
                        futures.append(executor.submit(queue(mirror, branch)))

                    elif branch == "arm-testing" and mirror.arm_testing_hash != master.arm_testing_hash:
                        futures.append(executor.submit(queue(mirror, branch)))

                    elif branch == "arm-unstable" and mirror.arm_unstable_hash != master.arm_unstable_hash:
                        futures.append(executor.submit(queue(mirror, branch)))
                    else:
                        print(f"Skip", branch)
            else:
                print("Skip", mirror.address, mirror.hash, master.hash)

            if not mirror.user_notified and not mirror.http and not mirror.https:
                    print("Mirror down", mirror.address)
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
                    mirror.save()
                    
        end = time.time()
        elapsed = end - start
        seconds = elapsed % (24 * 3600)
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        print("time: %d:%02d" % (minutes, seconds))

def check_offline_mirrors():
    mirrors = Mirror().query.filter_by(active=False).all()
    for mirror in mirrors:      
        for protocol in mirror.get_protocols():
            server = state_check(protocol, mirror.address)
            if server["state_file_exists"]:
                mirror.speed = server["access_time"]
                mirror.user_notified = False
                mirror.active = True
            
                if "https" in protocol:
                    mirror.https = server["state_file_exists"]
                elif "http" in protocol:
                    mirror.http = server["state_file_exists"]
                    
        if mirror.active:
            from src.utils.email import send_email
            from src.account.models import Account
            user = Account.query.get(mirror.account_id)
            send_email(
                user.email,
                "Your mirror is back online",
                f"Your Manjaro mirror {mirror.address}, has been activated."
                )
            
        else:
            if mirror.points >= 1:
                    mirror.points = mirror.points - 1
                    
        mirror.save()

def check_unsync_mirrors():
    mirrors = Mirror().query.filter_by(active=True).all()
    from src.utils.email import send_email
    from src.account.models import Account
    for mirror in mirrors:
        user = Account.query.get(mirror.account_id)
        if mirror.is_out_sync():
            def remove_point():
                if mirror.points >= 1:
                    mirror.points = mirror.points - 1
                    mirror.save()

            print("Outdated:", mirror.address, mirror.is_outdated_by(), mirror.last_sync_date())
            subject = f"Mirror out of sync for {mirror.is_outdated_by()} days"
            message = f"Your Manjaro mirror {mirror.address}, is outdated for {mirror.is_outdated_by()} days"
            msg_deleted = "and is now deleted."
            if mirror.is_outdated_by() == 999:
                msg = f"Your mirror {mirror.address} is missing state files"
                mirror.delete()
                send_email(
                    user.email,
                    msg,
                    f"{msg} {msg_deleted}"
                    )
                
            elif mirror.is_outdated_by() >= 14:
                mirror.delete()
                send_email(
                    user.email,
                    subject,
                    f"{message} {msg_deleted}"
                    )
                
            elif mirror.is_outdated_by() >= 7:
                remove_point()
                send_email(
                    user.email,
                    subject,
                    f"{message} and will be deleted from the poll after 14 days."
                    )
                
            elif mirror.is_outdated_by() == 1:
                remove_point()
                send_email(
                    user.email,
                    subject,
                    message
                    ) 
            
            elif mirror.is_outdated_by() >= 1 and mirror.is_outdated_by() <= 14:
                remove_point()
            else:
                if mirror.points != settings["MAX_POINTS"]:
                    mirror.points = mirror.points + 1
                    mirror.save()

def populate_master_state():
    branches = settings["BRANCHES"]
    repo = settings["MASTER_RSYNC"]
    master_mirror = MasterRepo().query.first()
    if not master_mirror:
        master_mirror = MasterRepo()

    protocol = "https"
    server = state_check(protocol, address=repo)
    file = get_state_contents(server["state_file"])
    master_mirror.hash = file["hash"]
    master_mirror.last_sync = file["last_sync"]
    master_mirror.save()
    print(master_mirror.hash)
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
            account.delete()
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
            
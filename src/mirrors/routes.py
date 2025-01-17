from flask import Blueprint, render_template, redirect, url_for, request, flash
from src.mirrors.models import Mirror
from src.utils.extensions import db
from flask_login import current_user, login_required
from flask import make_response
from src.utils.decorators import check_is_confirmed
from src.utils.config import settings
from src.mirrors.utils import test_country, sanitize_url
import json

mirror = Blueprint("mirror", __name__)

def _iter_mirrors():
    query = Mirror().query.filter_by(active=True).all()
    mirrors = []
    for mirror in query:
        country = mirror.country.replace(" ", "_")
        if "russian" in country:
            country = "russia"

        template = {
        "country": country,
        "url": mirror.address,
        "protocols": mirror.protocols(),
        "branches": [],
        "speed": mirror.speed,
        "last_sync": f"{mirror.last_sync_date()} {mirror.last_sync_time()}",
        "score": mirror.points           
        }
        
        if not mirror.stable_in_sync():
            template["branches"].append(0)
        else:
            template["branches"].append(1)
        
        if not mirror.testing_in_sync():
            template["branches"].append(0)
        else:
            template["branches"].append(1)

        if not mirror.unstable_in_sync():
            template["branches"].append(0)
        else:
            template["branches"].append(1)
            
        if not mirror.arm_stable_in_sync():
            template["branches"].append(0)
        else:
            template["branches"].append(1)
        
        if not mirror.arm_testing_in_sync():
            template["branches"].append(0)
        else:
            template["branches"].append(1)

        if not mirror.arm_unstable_in_sync():
            template["branches"].append(0)
        else:
            template["branches"].append(1)            
        
        mirrors.append(template)

    response = make_response(
        json.dumps(mirrors)
        )
    response.headers["Content-Type"] = "application/json"
    response.status_code = 200
    return response
    
@mirror.route("/status.json")
def status():
    response =_iter_mirrors()
    return response

@mirror.route("/mirrors")
@login_required
@check_is_confirmed
def my_mirrors():
    return render_template('mirrors.html', mirrors=current_user.mirror)

@mirror.route("/mirrors/rsync")
@login_required
@check_is_confirmed
def rsync_mirrors():
    query = Mirror().query.filter_by(rsync=True).all()
    mirrors = []
    master = settings["MASTER_RSYNC"]
    for mirror in query:
        if mirror.address != master:
            mirrors.append(mirror)
    
    return render_template('rsync.html', mirrors=mirrors, total=len(mirrors), master=master)

@mirror.route('/mirrors', methods=['POST'])
@login_required
@check_is_confirmed
def mirror_post():
    mirror_id = request.form.get('mirror-id')
    mirror_validation_token = request.form.get('validate-mirror')
    if mirror_validation_token:
        from src.mirrors.utils import validate_ownership
        mirror = Mirror.query.get(mirror_id)

        is_valid = validate_ownership(mirror.get_protocol(), mirror.address, mirror_validation_token)
        if is_valid:
            mirror.account_id = current_user.id
            mirror.save()
            flash(f'Mirror has been added to you account')
            return redirect(url_for('mirror.my_mirrors'))
        else:
            flash(f'File not found, mirror validation failed', "warning")
            return render_template('mirror_exists.html', mirror=mirror, file_name=mirror_validation_token)
    else:
        if mirror_id:
            delete_mirror = request.form.get(f'delete-mirror-{mirror_id}')
            active = request.form.get('active')
            mirror = Mirror.query.get(mirror_id)

            if delete_mirror:
                mirror.delete()
                flash(f'Mirror Deleted')
                return redirect(url_for('mirror.my_mirrors'))

            if active and mirror_id:
                mirror.active = True
                mirror.user_notified = False
                mirror.save()
                flash(f'Mirror Enabled')
                return redirect(url_for('mirror.my_mirrors'))

            elif not active and mirror_id:
                mirror.active = False
                mirror.save()
                flash(f'Mirror Disabled', "warning")
                return redirect(url_for('mirror.my_mirrors'))
            
        else:    
            address = request.form.get('mirror')
            country = request.form.get('country').lower()    
            from src.mirrors.utils import state_check
            address = sanitize_url(address)

            if not address:
                flash('Please insert a mirror address', "error")
                return redirect(url_for('mirror.my_mirrors'))

            address_exists = Mirror.query.filter_by(address=address).first()
            if address_exists:
                import secrets
                token = secrets.token_hex(8)
                return render_template('mirror_exists.html', mirror=address_exists, file_name=token)
            
            protocols = {
                "http": False,
                "https": False,
                "rsync": False
            }
            
            for protocol in protocols:
                if "http" in protocol:
                    server = state_check(protocol, address)
                    if server["state_file_exists"]:
                        protocols[protocol] = server["state_file_exists"]
                        ip = server["ip"]
                else:
                    from src.mirrors.utils import test_rsync
                    rsync = test_rsync(address)
                    if rsync:
                        protocols["rsync"] = rsync
                    

            if any(val == True for val in protocols.values()):
                pass
            else:
                flash('Something is wrong, or server does not exist', "error")
                return redirect(url_for('mirror.my_mirrors'))
                                                   
            db.session.add(
                Mirror(
                address=sanitize_url(address),
                account_id=current_user.id,
                country=test_country(country),
                rsync=protocols["rsync"],
                active=True,
                http=protocols["http"],
                https=protocols["https"],
                speed = server["access_time"],
                ip_whitelist=ip
                )
            )
            
            db.session.commit()           
            flash('Thank you, mirrors are updated', "success")       
            return redirect(url_for('mirror.my_mirrors'))

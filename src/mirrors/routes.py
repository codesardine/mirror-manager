from flask import Blueprint, render_template, redirect, url_for, request, flash
from ..mirrors.models import Mirror
from ..utils.extensions import db
from flask_login import current_user, login_required
from flask import make_response
from src.utils.decorators import check_is_confirmed
import json

mirror = Blueprint("mirror", __name__)

@mirror.route("/mirrors.json")
def mirrors():
    query = Mirror().query.filter_by(active=True).all()
    mirrors = []
    for mirror in query:
        if mirror.last_sync is not None:
            protocols = []
            template = {
            "country": mirror.country,
            "url": mirror.address,
            "protocols": protocols
            }
            if mirror.http:
                protocols.append("http")
            if mirror.https:
                protocols.append("https")
            if mirror.rsync:
                protocols.append("rsync")

            mirrors.append(template)

    response = make_response(
        json.dumps(mirrors)
        )
    response.headers["Content-Type"] = "application/json"
    response.status_code = 200
    return response


@mirror.route("/mirrors")
@login_required
@check_is_confirmed
def my_mirrors():
    return render_template('mirrors.html', mirrors=current_user.mirror)

@mirror.route('/mirrors', methods=['POST'])
@login_required
@check_is_confirmed
def mirror_post():
    mirror_id = request.form.get('mirror-id')
    if mirror_id:
        delete_mirror = request.form.get(f'delete-mirror-{mirror_id}')
        active = request.form.get('active')
        mirror = Mirror.query.get(mirror_id)

        if delete_mirror:
            db.session.delete(mirror)
            db.session.commit()
            flash(f'Mirror Deleted')
            return redirect(url_for('mirror.my_mirrors'))

        if active and mirror_id:
            mirror.active = True
            mirror.user_notified = False
            db.session.add(mirror)
            db.session.commit()
            flash(f'Mirror Enabled')
            return redirect(url_for('mirror.my_mirrors'))

        elif not active and mirror_id:
            mirror.active = False
            db.session.add(mirror)
            db.session.commit()
            flash(f'Mirror Disabled', "warning")
            return redirect(url_for('mirror.my_mirrors'))
        
    else:    
        address = request.form.get('mirror')
        ip_whitelist = request.form.get('ip-whitelist')
        country = request.form.get('country')    
        import pycountry
        from src.mirrors.utils import state_check

        def sanitize_url(url):
            if not address.endswith("/"):
                url = address + "/"

            if "http" in url:
                url = url.split("://")[1]

            return url

        address = sanitize_url(address)
        if not address:
            flash('Please insert a mirror address', "error")
            return redirect(url_for('mirror.my_mirrors'))

        address_exists = Mirror.query.filter_by(address=address).first()
        if address_exists:
            flash('This mirror already exists', 'error')
            return redirect(url_for('mirror.my_mirrors'))
        
        protocols = {
            "http": False,
            "https": False,
            "rsync": False
        }
        
        speed = 0
        for protocol in protocols:
            if "http" in protocol:
                server = state_check(protocol, address)
                if server["state_file_exists"]:
                    protocols[protocol] = server["state_file_exists"]
                    speed = server["access_time"]
            else:
                import subprocess
                cmd = ["rsync", f"rsync://{address}"]
                try:
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                    result = proc.returncode
                    if result == 0:
                        protocols["rsync"] = True  
                except subprocess.TimeoutExpired:
                    pass

        if any(val == True for val in protocols.values()):
            pass
        else:
            flash('Something is wrong, or server does not exist', "error")
            return redirect(url_for('mirror.my_mirrors'))

        try:
            is_country = pycountry.countries.get(name=country)
            if not is_country:
                flash(f'Invalid country "{country}"', "error")
                return redirect(url_for('mirror.my_mirrors'))

        except:
            flash('Invalid country', "error")
            return redirect(url_for('mirror.my_mirrors'))                          
        
        flash('Thank you, mirrors are updated', "success")

        db.session.add(
            Mirror(
            address=sanitize_url(address),
            account_id=current_user.id,
            country=country.lower(),
            rsync=protocols["rsync"],
            active=True,
            http=protocols["http"],
            https=protocols["https"],
            speed = speed,
            ip_whitelist=ip_whitelist
            )
        )
        db.session.commit()
        return redirect(url_for('mirror.my_mirrors'))

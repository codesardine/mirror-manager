#!/usr/bin/env python
from src import db, app
import sys

        
if "create-db" in sys.argv:
    with app.app_context():
        db.create_all()

if "delete-db" in sys.argv:
    with app.app_context():
        db.drop_all()

if "import-mirrors" in sys.argv:
    with app.app_context():
        from src.mirrors.models import Mirror
        from src.mirrors.utils import test_rsync, test_country, sanitize_url, state_check
        import requests
        headers = {'Accept': 'application/json'}
        response = requests.get('https://repo.manjaro.org/status.json', headers=headers)
        mirrors = response.json()

        for mirror in mirrors:
            url = sanitize_url(mirror["url"])  
            for p in mirror["protocols"]:
                if p == "https":
                    https = True
                    pass

                if p == "http":
                    http = True

            
            mirror_exists = Mirror().query.filter_by(address=url).first()
            if not mirror_exists:
                if not "global" in mirror["country"].lower():
                    country = test_country(mirror["country"].replace("_", " "))
                else:
                    try:
                        country = mirror.country
                    except AttributeError:
                        print("error", mirror)
                        country = "unknown"

                if https:
                    status = state_check("https", url)
                else:
                    status = state_check("http", url)

                try:
                    ip = status["ip"]                
                    db.session.add(
                        Mirror(
                        address=url,
                        account_id=1,
                        country=country,
                        rsync=test_rsync(url),
                        active=True,
                        http=http,
                        https=https,
                        speed = 0,
                        ip_whitelist=ip,
                        in_sync=True
                        )
                    )
                
                    db.session.commit()
                except Exception as e:
                    print(e, status)

        

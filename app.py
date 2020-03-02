# This is a demo app which has been created using the following post
# https://blog.miguelgrinberg.com/post/using-celery-with-flask

from flask import Flask, request
from celery import Celery
from flask_httpauth import HTTPBasicAuth
from modules.demo import asa_og
import config as cfg
import json
import requests
import urllib3
import ipaddress
from datetime import datetime
from uuid import uuid4

# Disable the annoying insecure warnings from the requests module due to
# NSX Manager not having a CA signed certificate in ab scenarios
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'amqp://localhost'
app.config['CELERY_RESULT_BACKEND'] = 'rpc://localhost'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Used for authenticating the flask API
auth = HTTPBasicAuth()

# Used for querying the NSX Manager API
basicAuthCredentials = (cfg.NSX_MANAGER_USERNAME, cfg.NSX_MANAGER_PASSWORD)
headers = {
    "Content-Type": "Application/json"
}

# Dictionary to hold API auth credentials
USER_DATA = {
    cfg.API_NOTIFICATION_USERNAME: cfg.API_NOTIFICATION_PASSWORD
}

# Celery task that is invoked when a notification is received from NSX Manager.


@celery.task
def GetGroupTranslation(path):
    # Create a unique string and
    updateid = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-') + str(uuid4())
    playbook_file = '%s.yaml' % (updateid)
    playbook_log = '%s.log' % (updateid)

    # Initiate lists to build that contain the IP Addresses and networks
    hosts = list()
    networks = list()

    # Query the NSX Manager groups for the translated IP addresses
    r = requests.get('https://%s%s/members/ip-addresses' % (cfg.NSX_MANAGER_IP,
                                                            path), auth=basicAuthCredentials, headers=headers, verify=False)
    if r.status_code == 200:
        print(r.text)
        data = json.loads(r.text)

        # Work through the response and populate the host and network lists
        for address in data['results']:
            ip = ipaddress.ip_network(address)
            if ip.version == 4:
                if ip.num_addresses == 1:
                    hosts.append(str(ip.network_address))
                    print('Added host: %s to hosts list' %
                          (ip.network_address))
                else:
                    networks.append('%s %s' %
                                    (str(ip.network_address), str(ip.netmask)))
                    print('Added network: %s %s to networks list' %
                          (str(ip.network_address), str(ip.netmask)))
            else:
                # The asa_og module does not support IPv6 addressing yet.
                # But this is just a demo, so no need for it yet.
                print('Skipped address: %s as it is not an IPv4 address' %
                      (address))

        # Create and execute ansible playbooks to update ASA object groups
        x = asa_og(hosts, networks, path)
        x.create_playbook()
        x.save_playbook(playbook_file)
        x.execute_playbook(playbook_file, playbook_log)


@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password


@app.route(cfg.API_NOTIFICATION_URI, methods=['POST'])
@auth.login_required
def notifications():
    payload = json.dumps(request.get_json())
    print(payload)
    data = json.loads(payload)
    if data['refresh_needed'] == True:
        pass
        # When the refresh_needed flag is set to true, this indicates that
        # the server should fetch the updated information from all the
        # groups that it is watching. To do this, you would query the
        # notification watcher API for this watcher, parse it for all the
        # watched groups, and then retrieve the updated information for all
        # the groups.
    if data['result_count'] > 0:
        for item in data['results'][0]['uris']:
            print(item['uri'])
            GetGroupTranslation.delay(item['uri'])
    return json.dumps({'accepted': True}), 202, {'ContentType': 'application/json'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)

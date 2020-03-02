import yaml
from datetime import datetime
from uuid import uuid4
import os
import subprocess
import config as cfg


class asa_og:
    def __init__(self, hosts, networks, path):
        self.hosts = hosts
        self.networks = networks
        self.path = path
        self.group = None
        self.playbook_details = None
        self.module_details = None
        self.task_details = None
        self.playbook = None

    def get_hosts(self):
        return self.hosts

    def get_networks(self):
        return self.networks

    def get_path(self):
        return self.path

    def get_group(self):
        self.group = os.path.basename(self.path)
        return self.group

    def get_playbook_details(self):
        return self.playbook_details

    def get_module_details(self):
        return self.module_details

    def get_task_details(self):
        return self.task_details

    def get_playbook(self):
        return self.playbook

    def create_playbook_details(self):
        playbook_details = {}
        playbook_details.update({'name': cfg.OBJECT_GROUP_PLAYBOOK_NAME})
        playbook_details.update({'connection': 'network_cli'})
        playbook_details.update({'hosts': cfg.INVENTORY_HOSTS_GROUP})
        playbook_details.update({'gather_facts': False})
        self.playbook_details = playbook_details

    def create_module_details(self):
        module_details = {}

        # Fill in the module details
        module_details.update({'name': self.get_group()})
        module_details.update({'group_type': 'network-object'})
        module_details.update({'state': 'replace'})
        if len(self.get_hosts()) > 0:
            module_details.update({'host_ip': self.get_hosts()})
        if len(self.get_networks()) > 0:
            module_details.update({'ip_mask': self.get_networks()})
        self.module_details = module_details

    def create_task(self):
        task_item = {}
        self.create_module_details()
        # Add the details as a task
        task_item.update(
            {'name': 'Configure object-group %s' % (self.get_group())})
        task_item.update({'asa_og': self.get_module_details()})
        self.task_details = task_item

    def create_playbook(self):
        playbook = list()
        tasksList = list()

        self.create_playbook_details()
        playbook_details = self.get_playbook_details()

        self.create_task()
        tasksList.append(self.get_task_details())
        playbook_details.update({'tasks': tasksList})

        playbook.append(playbook_details)
        self.playbook = playbook

    def save_playbook(self, filename):
        if not os.path.exists(cfg.PLAYBOOKS_DIR_NAME):
            os.makedirs(cfg.PLAYBOOKS_DIR_NAME)
        filename = os.path.join(cfg.PLAYBOOKS_DIR_NAME, filename)
        with open(filename, 'w') as outfile:
            yaml.dump(self.get_playbook(), outfile, default_flow_style=False)

    def execute_playbook(self, filename, logfile):
        if not os.path.exists(cfg.PLAYBOOKS_DIR_NAME):
            os.makedirs(cfg.PLAYBOOKS_DIR_NAME)
        filename = os.path.join(cfg.PLAYBOOKS_DIR_NAME, filename)
        logfile = os.path.join(cfg.PLAYBOOKS_DIR_NAME, logfile)
        os.environ["ANSIBLE_LOG_PATH"] = logfile
        subprocess.run(["ansible-playbook", "-i",
                        cfg.INVENTORY_FILE, filename, "-vvvv"])
        del os.environ["ANSIBLE_LOG_PATH"]


def main():

    # Generate string to be used for playbooks and logfiles
    updateid = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-') + str(uuid4())
    playbook_file = '%s/%s.yaml' % (cfg.PLAYBOOKS_DIR_NAME, updateid)
    playbook_log = '%s/%s.log' % (cfg.PLAYBOOKS_DIR_NAME, updateid)
    hostIpList = ['33.33.133.33', '44.44.44.44']
    networks = []
    path = '/policy/api/v1/infra/domains/default/groups/testGroup'
    x = asa_og(hostIpList, networks, path)
    x.create_playbook()
    x.save_playbook(playbook_file)
    x.execute_playbook(playbook_file, playbook_log)


if __name__ == '__main__':
    main()

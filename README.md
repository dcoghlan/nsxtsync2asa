# NSX-T Sync2ASA

A sample application that receives group notification updates from NSX-T and configures the appropriate network object-groups in a Cisco ASA (virtual or physical) using Ansible.

More information about how to use this sample app can be found at the following link:  
<https://www.sneaku.com/2020/03/02/how-to-sync-a-dynamic-nsx-t-group-to-an-external-system/>

## Clone the repository

- `git clone https://github.com/dcoghlan/nsxtsync2asa.git`

## Installations for Ubuntu 18.04

- `apt-get -y install python3-pip python-celery-common`
- `cd nsxtsync2asa`
- `pip3 install -r requirements.txt`
- RabbitMQ
  - <https://www.rabbitmq.com/install-debian.html#apt-bintray-quick-start>

## Configure Ansible Inventory

- The repository has a sample configuration to work with a single ASAv. The details for the ASAv are configured in the `inventory` file. Update the details in this file to apply to your specific environment.

## Setup NSX-T Notification Watcher

- NSX-T will need to have a notification watcher configured.
  - server = IP address of the Ubuntu 18.04 server
  - uri = defined by the variable `API_NOTIFICATION_URI` in `./config.py`
  - username = defined by the variable `API_NOTIFICATION_USERNAME` in `./config.py`
  - password = defined by the variable `API_NOTIFICATION_PASSWORD` in `./config.py`

```json
POST /api/v1/notification-watchers

{
  "server": "10.0.0.1",
  "method": "POST",
  "uri": "/nsx-notifications",
  "authentication_scheme": {
      "scheme_name": "BASIC_AUTH",
      "username":  "nsx_notification_user",
      "password": "eZHc7k5Z7Gsa"
    }
}
```

- Add the required policy group subscriptions to the notification watcher
  - watcher-id = ID of notification watcher created above. (Perform a `GET` on `/api/v1/notification-watchers/` to view all notification watchers configured.)
  - uri_filters = policy path of the group to watch. For all groups use `/policy/api/v1/infra/domains/default/groups/*`

```json
POST /api/v1/notification-watchers/<watcher-id>/notifications?action=add_uri_filters

{
    "notification_id" : "group.change_notification",
    "uri_filters" : [ "/policy/api/v1/infra/domains/default/groups/RFC1918" ]
  }
```

## Run Application

- change directory into the folder that app.py has been extracted into
- start the celery worker as a background task

```bash
./worker.sh start
```

- start the flask app

```bash
sudo python3 app.py
```

## Operations

- Restart celery worker
  - The celery workers are required to be restarted upon ANY change to the files in this repository as the configuration is loaded only when the celery workers are started.

```bash
./worker.sh stop
./worker.sh start
```

## Sample Notification Messages

### Group Deletion

```json
{
  "results": [
    {
      "notification_id": "group.change_notification",
      "uris": [
        {
          "uri": "/policy/api/v1/infra/domains/default/groups/RFC1918",
          "operation": "DELETE"
        }
      ]
    }
  ],
  "refresh_needed": false,
  "result_count": 1
}
```

### Group Update

```json
{
  "result_count": 2,
  "refresh_needed": false,
  "results": [
    {
      "notification_id": "group.change_notification",
      "uris": [
        {
          "operation": "UPDATE",
          "uri": "/policy/api/v1/infra/domains/default/groups/Linux-Hosts"
        },
        {
          "operation": "UPDATE",
          "uri": "/policy/api/v1/infra/domains/default/groups/RFC1918"
        }
      ]
    }
  ]
}
```

### Refresh required

```json
{
  "results": [],
  "refresh_needed": true,
  "result_count": 0
}
```

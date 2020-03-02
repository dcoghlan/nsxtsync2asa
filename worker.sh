#!/bin/sh

case "$1" in
    start)
        celery multi start -A app.celery worker --loglevel=DEBUG --logfile=logs/celery.log ;;
    stop) celery multi stop 1 --pidfile=worker.pid ;;
    *)
        shift
        # servicenames=${@-servicenames}
        echo "usage: $0 [start|stop]"
        exit 1
esac

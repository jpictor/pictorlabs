#!/bin/bash

## the name of this service
SERVICE_NAME=pictorlabs
SERVICE_PORT=9193

## need this to resolve symlinks
pushd . > /dev/null
SCRIPT_PATH="${BASH_SOURCE[0]}";
while([ -h "${SCRIPT_PATH}" ]) do
  cd "`dirname "${SCRIPT_PATH}"`"
  SCRIPT_PATH="$(readlink "`basename "${SCRIPT_PATH}"`")";
done
cd "`dirname "${SCRIPT_PATH}"`" > /dev/null
SCRIPT_PATH="`pwd`";
popd  > /dev/null

export SERVICE_ROOT="${SCRIPT_PATH}"

## python program
export PYTHON=python

## add src/ directory to PYTHONPATH
export PYTHONPATH=${SERVICE_ROOT}/src

## number of worker processes
NUM_WORKERS=10
MAX_TASKS_PER_CHILD=10000

## uid/gid to run server as if invoked by root
if [ "$(id -u)" == "0" ]; then
  if [ -z "${SERVICE_UID}" ]; then
    SERVICE_UID=www-data
  fi
  if [ -z "${SERVICE_GID}" ]; then
    SERVICE_GID=www-data
  fi
  CELERY_UID_ARGS="--uid=${SERVICE_UID} --gid=${SERVICE_GID}"
fi

## Celery options
CELERY_LOGLEVEL=INFO

## build virtual python environment
function build_vpython {
        echo "Building in ${SERVICE_ROOT}..."
        cd ${SERVICE_ROOT}
        rm -rf vpython
        virtualenv vpython
        source ${SERVICE_ROOT}/vpython/bin/activate
        pip --version
        pip install -U pip
        pip install -U setuptools
        pip install -U distribute
        echo "Installing requirements.txt..."
        pip install -r requirements.txt
}

## build AngularJS app
function build_angular_app {
        pushd angular_app
        bower install
        popd
}

## build static dir
function build_collectstatic {
        ${SERVICE_ROOT}/manage.sh collectstatic --noinput
}

case "$1" in
    build_all)
        set -e
        build_vpython
        build_angular_app
        build_collectstatic
        ;;
    build_vpython)
        set -e
        build_vpython
        ;;
    create_rabbitmq_account)
        rabbitmqctl add_user ${SERVICE_NAME}_user password
        rabbitmqctl add_vhost ${SERVICE_NAME}_vhost
        rabbitmqctl set_permissions -p ${SERVICE_NAME}_vhost ${SERVICE_NAME}_user ".*" ".*" ".*"
        rabbitmqctl add_user ${SERVICE_NAME}_testuser password
        rabbitmqctl add_vhost ${SERVICE_NAME}_testvhost
        rabbitmqctl set_permissions -p ${SERVICE_NAME}_testvhost ${SERVICE_NAME}_testuser ".*" ".*" ".*"
    ;;
    exec)
        export DJANGO_SETTINGS_MODULE=baseapp.settings
        shift 1
        exec "$@"
	;;
    python)
        shift 1
        export DJANGO_SETTINGS_MODULE=baseapp.settings
        exec ${PYTHON} "$@"
	;;
    celery_dev)
        exec celery worker \
            --app=baseapp.celery_ext.app \
            --autoscale=4,0 \
            --maxtasksperchild=10 \
            --loglevel=DEBUG \
            --schedule=${SERVICE_ROOT}/var/celerybeat.db \
            --pidfile=${SERVICE_ROOT}/var/celerybeat.pid \
            --beat
	;;
    celery_q_default)
        exec celery worker \
            --app=baseapp.celery_ext.app \
            --queues=baseapp \
            --autoscale=2,0 \
            --maxtasksperchild=${MAX_TASKS_PER_CHILD} \
            --loglevel=${CELERY_LOGLEVEL} \
            ${CELERY_UID_ARGS}
        ;;
    celerybeat_prod)
        exec celery beat \
            --app=baseapp.celery_ext.app \
            --schedule=${SERVICE_ROOT}/var/celerybeat.db \
            --pidfile=${SERVICE_ROOT}/var/celerybeat.pid \
            --loglevel=${CELERY_LOGLEVEL} \
            ${CELERY_UID_ARGS}
	;;
    flower)
        exec celery -A baseapp.celery_ext.app flower --loglevel=${CELERY_LOGLEVEL}
	;;
    rungu_dev)
        exec gunicorn \
                --bind=0.0.0.0:${SERVICE_PORT} \
                --workers=3 \
                --timeout=256 \
                --max-requests=${MAX_TASKS_PER_CHILD} \
                --log-config=${SERVICE_ROOT}/etc/logging_dev.ini \
                baseapp.wsgi:application
	;;
    rungu_prod)
        exec gunicorn \
                --bind=0.0.0.0:${SERVICE_PORT} \
                --workers=${NUM_WORKERS} \
                --user=${SERVICE_UID} \
                --group=${SERVICE_GID} \
                --timeout=256 \
                --keep-alive=30 \
                --max-requests=${MAX_TASKS_PER_CHILD} \
                --log-config=${SERVICE_ROOT}/etc/logging_prod.ini \
                --access-logfile=- \
                --error-logfile=- \
                baseapp.wsgi:application
        ;;
    *)
        export DJANGO_SETTINGS_MODULE=baseapp.settings
        export SERVICE_PORT=${SERVICE_PORT}
        exec ${PYTHON} ${SERVICE_ROOT}/etc/run_django.py "$@"
        ;;
esac

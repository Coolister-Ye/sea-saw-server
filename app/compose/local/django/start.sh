#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

python manage.py migrate
python manage.py runserver 0.0.0.0:8000
# python manage.py collectstatic --noinput
# gunicorn --bind 0.0.0.0:8000 sea_saw_server.wsgi:application

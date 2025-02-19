#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

python manage.py migrate
python manage.py collectstatic --noinput
gunicorn sea_saw_server.wsgi:application --bind 0.0.0.0:8000
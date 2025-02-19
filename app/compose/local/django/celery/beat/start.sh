#!/bin/bash

set -o errexit
set -o nounset

rm -f './celerybeat.pid'
celery -A sea_saw_server beat -l INFO
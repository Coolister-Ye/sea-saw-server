#!/bin/bash

set -o errexit
set -o nounset

watchfiles \
  --filter python \
  'celery -A sea_saw_server worker --loglevel=info'
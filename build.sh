#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
# Roda em todo deploy (sem precisar do Shell do Render)
python manage.py migrate --noinput

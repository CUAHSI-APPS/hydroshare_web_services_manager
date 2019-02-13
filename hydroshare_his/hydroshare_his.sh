#!/bin/bash

# Start Gunicorn processes
echo Activating Environment
source activate his
echo Collecting Static Files
python manage.py collectstatic --noinput

echo Starting Gunicorn.
exec gunicorn hydroshare_his.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3
#!/bin/bash


source /home/hisapp/miniconda2/bin/activate his

python /home/hisapp/hydroshare_his/manage.py collectstatic --noinput

/usr/bin/supervisord -c /home/hisapp/hydroshare_his/supervisord.conf

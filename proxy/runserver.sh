#!/bin/bash
sed -i '1s/.*/user nobody;/' /etc/nginx/nginx.conf
nginx
while :
do
    inotifywait -r -e close_write /etc/hosts && nginx -s reload
    sleep 1
done
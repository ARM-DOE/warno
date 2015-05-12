#!/bin/bash
service nginx restart
while :
do 
    inotifywait -r -e close_write /etc/hosts && service nginx restart
    sleep 1
done
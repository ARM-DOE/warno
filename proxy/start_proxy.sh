#!/usr/bin/env bash

cp /vagrant/proxy/nginx.conf /etc/nginx/nginx.conf
cp /vagrant/proxy/privkey.pem /etc/ssl/privkey.pem
cp /vagrant/proxy/cacert.pem /etc/ssl/cacert.pem

chmod a+x /vagrant/proxy/runserver.sh
chmod 711 /var/lib/nginx /var/lib/nginx/tmp

cp -r -T /vagrant/proxy/sites-enabled /etc/nginx/sites-enabled

/vagrant/proxy/runserver.sh >> /vagrant/logs/proxy_server.log 2>&1 &
disown

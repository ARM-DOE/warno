#! /usr/bin/env bash

if [ "$VAGRANT_HOME" = "" ]; then
    VAGRANT_HOME=/vagrant
fi

mkdir /opt/redis

cd /opt/redis

wget http://download.redis.io/redis-stable.tar.gz
echo "\n\n"
tar -xz --keep-newer-files -f redis-stable.tar.gz

cd redis-stable
make
make install

rm /etc/redis.conf
mkdir -p /etc/redis
mkdir /var/redis
chmod -R 777 /var/redis
useradd redis

cp -u $VAGRANT_HOME/redis/6379.conf /etc/redis/6379.conf
cp -u $VAGRANT_HOME/redis/redis_6379 /etc/init.d/redis_6379

systemctl enable redis_6379

chmod a+x /etc/init.d/redis_6379
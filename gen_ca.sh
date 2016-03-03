#!/usr/bin/env bash
# Source http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

openssl genrsa -out $DIR/rootCA.key 2048
openssl req -x509 -new -nodes -key $DIR/rootCA.key -sha256 -out $DIR/rootCA.pem
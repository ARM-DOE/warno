#!/usr/bin/env bash
# Source http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

openssl genrsa -out $DIR/proxy/privkey.pem 2048
openssl req -new -key $DIR/proxy/privkey.pem -out $DIR/privreq.csr
openssl x509 -req -in $DIR/privreq.csr -CA $DIR/data_store/data/rootCA.pem -CAkey $DIR/data_store/data/rootCA.key -CAcreateserial -out $DIR/proxy/cacert.pem -days 1095 -sha256

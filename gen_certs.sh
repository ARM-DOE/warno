#!/usr/bin/env bash
openssl genrsa -out privkey.pem 2048
openssl req -new -key proxy/privkey.pem -out privreq.csr
openssl x509 -req -in privreq.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out proxy/cacert.pem -days 1095 -sha256

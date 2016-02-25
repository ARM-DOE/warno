#!/usr/bin/env bash
openssl genrsa -out proxy/privkey.pem 2048
openssl req -new -x509 -key proxy/privkey.pem -out proxy/cacert.pem -days 1095

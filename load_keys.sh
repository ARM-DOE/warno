#! /usr/bin/env bash
PRIVATE_KEY="/vagrant/id_rsa"
PUBLIC_KEY="/vagrant/id_rsa.pub"

if [[ -f $PRIVATE_KEY ]]; then
    echo "Loading $PRIVATE_KEY"
    cp $PRIVATE_KEY ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
fi

if [[ -f $PRIVATE_KEY ]]; then
    echo "Loading $PUBLIC_KEY"
    cp $PRIVATE_KEY ~/.ssh/id_rsa.pub
    chmod 644 ~/.ssh/id_rsa.pub
fi
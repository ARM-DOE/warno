#! /usr/bin/env bash

if [ "$VAGRANT_HOME" = "" ]; then
    VAGRANT_HOME=/vagrant
fi

PRIVATE_KEY="$VAGRANT_HOME/id_rsa"
PUBLIC_KEY="$VAGRANT_HOME/id_rsa.pub"

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
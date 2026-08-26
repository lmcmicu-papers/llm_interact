#!/usr/bin/env bash

if [ ! -z $INTERACT_CONTAINER ]
then
    container=$INTERACT_CONTAINER
else
    if [ $# -ne 1 ]
    then
	      echo "Usage: $(basename $0) CONTAINER"
        echo "(or set the container using the INTERACT_CONTAINER environment variable)"
	      exit 1
    fi
    container=$1
fi

docker exec -it $container bash

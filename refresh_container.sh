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
	shift
fi

if [[ $1 == "--hard" ]]
then
	echo "Restarting $container ..."
	docker restart ${container} || exit 1
fi

docker cp Makefile ${container}:/
docker cp requirements.txt ${container}:/
docker cp README.md ${container}:/
docker cp readme_dirty.sh ${container}:/
for pyfile in src/*.py
do
  docker cp $pyfile ${container}:/src/
done
for datafile in data/*
do
  docker cp $datafile ${container}:/data/
done

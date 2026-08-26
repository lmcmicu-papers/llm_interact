#!/usr/bin/env bash

##
# llm_interact - a handy tool for communicating with Ollama LLM models using Python
# Copyright (C) 2025 Michael E. Cuffaro
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
##

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

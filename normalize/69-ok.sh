#!/usr/bin/env bash

if [ "$#" -eq 0 ]; then
    echo "69-ok folders"
fi

#for i; do
#    if [ -d "$i" ] ; then
#        echo "$i is not a folder"
#    else
#        touch "$i/.69-ok"
#    fi
#done

ARG=$*
if [ -d "$ARG" ] ; then
    touch "$ARG/.69-ok"
else
    echo "$ARG is not a folder"
fi

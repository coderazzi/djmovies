#!/bin/bash

if [[ "$#" -eq 3 ]]; then
    echo "mkvpropedit $1 --edit track:$3 --set language=$2"
    mkvpropedit $1 --edit track:$3 --set language=$2
else
    echo "set-language.sh filename language track"
fi

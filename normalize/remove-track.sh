#!/bin/bash

if [[ ( "$#" -lt 2 ) || (( "$#" -gt 3 ) || ( "$3" -ne "UNDO" )) ]]; then
    echo "remove-track.sh filename track [UNDO]"
fi

COMMENT="TO-REMOVE"

if [[ "$#" -eq 3 ]]; then
    COMMENT=""
fi

mkvpropedit $1 --edit track:$2 --set name="$COMMENT"

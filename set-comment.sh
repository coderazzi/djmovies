#!/bin/bash

if [[ ( "$#" -lt 2 ) || ( "$#" -gt 3 ) ]]; then
    echo "set-comment.sh filename track [comment]"
    exit
fi

COMMENT="Commentary"

if [[ "$#" -eq 3 ]]; then
    COMMENT="$COMMENT - $3"
fi

mkvpropedit $1 --edit track:$2 --set name="$COMMENT"

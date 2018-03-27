#!/usr/bin/env bash

if [ "$#" -eq 0 ]; then
    echo "concat folder|[-a|-n name]files"
    exit 1
fi

if [ "$#" -eq 1 ]; then
    if [ -d "$1" ] ; then
        OUTPUT=$1  # output matches folder name, extension will be added later
        TMP_FILE=$(mktemp /tmp/69.XXXXXX)
        while read each; do
            F=`echo $1/$each | sed "s/'/\\'\\\\\\'\\'/g"`
            echo "file '$F'" >> $TMP_FILE;
            ANY=$each;
        done < <(ls "$1")
    else
        echo "$1 is not a folder"
        exit 1
    fi
else
    if [[ $1 == -a* ]] ; then
        REMOVE_CONCATS=1
        NAME=${1:2}
        shift
        #OUTPUT=`dirname "$1"`
        # note: if args where only -a, would have tried to handle it as a folder :-)
        if [ -z "$NAME" ] ; then
            OUTPUT="${1%.*}concat"
        else
            OUTPUT=`dirname "$1"`
            OUTPUT="${OUTPUT}/${NAME}"
        fi
    else
        OUTPUT=`dirname "$1"`
    fi
    ANY=$1
    TMP_FILE=$(mktemp /tmp/69.XXXXXX)
    for i; do
        F=`echo $i | sed "s/'/\\'\\\\\\'\\'/g"`
        echo "file '$F'" >> $TMP_FILE;
    done
fi

#add now the extension to variable OUTPUT
filename=$(basename "$ANY")
OUTPUT="$OUTPUT.${filename##*.}"

if [ -f "$OUTPUT" ] ; then
    echo "Output file already $OUTPUT already exists"
    exit 1
fi

echo ffmpeg -f concat -safe 0 -i $TMP_FILE -c copy "$OUTPUT"
ffmpeg -f concat -safe 0 -i $TMP_FILE -c copy "$OUTPUT" | exit 1

rm -Rf $TMP_FILE
if [ ! -z "$REMOVE_CONCATS" ] ; then
    for i; do
        rm "$i"
    done
fi
echo "Concat Output Path: $OUTPUT"
#exit 0
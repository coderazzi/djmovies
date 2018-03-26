#!/usr/bin/env bash

if [ "$#" -eq 0 ]; then
    echo "concat folder|files"
fi

if [ "$#" -eq 1 ]; then
    if [ -d "$1" ] ; then
        OUTPUT=$1
        TMP_FILE=$(mktemp /tmp/69.XXXXXX)
        while read each; do echo "file '$1/$each'" >> $TMP_FILE; ANY=$each; done < <(ls "$1")
    else
        echo "$1 is not a folder"
        exit 1
    fi
else
    TMP_FILE=$(mktemp /tmp/69.XXXXXX)
    OUTPUT=`dirname "$1"`
    ANY=$1
    for i; do echo "file '$i'" >> $TMP_FILE; done
fi

filename=$(basename "$ANY")
OUTPUT="$OUTPUT.${filename##*.}"

if [ -f "$OUTPUT" ] ; then
    echo "Output file already $OUTPUT already exists"
    exit 1
fi

echo ffmpeg -f concat -safe 0 -i $TMP_FILE -c copy "$OUTPUT"
ffmpeg -f concat -safe 0 -i $TMP_FILE -c copy "$OUTPUT" | exit 1

rm -Rf $TMP_FILE
echo "Concat Output Path: $OUTPUT"
exit 0
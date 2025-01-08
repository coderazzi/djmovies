#!/bin/bash

TARGET='/home/coderazzi/Dropbox/backups'
if [ ! -d "$TARGET" ] ; then
  TARGET='/Users/coderazzi/Dropbox/backups'
  if [ ! -d "$TARGET" ] ; then
    echo No $TARGET folder found
    exit 1
  fi
fi

DATABASE=db_movies.sqlite

cd `dirname $0`

next=1
for f in $TARGET/djmovies.*.sqlite ; do
	# number=$(echo $f | grep -Eo '[1-9]\d*')
	number=$(echo $f | grep -Eo '[1-9][0-9]*')
	number=$((number+1))
	if [ $number -gt $next ] ; then
		next=$number
		last=$f
	fi
done

copy=1
echo Current database backup is $last

if [ -n "$last" ] ; then
	if diff -q $last $DATABASE > /dev/null ; then
  		copy=0
	fi	
fi

if [ "$copy" -eq 1 ] ; then
	target=$TARGET/djmovies.$next.sqlite
	cp db_movies.sqlite $target
	echo Created $target
else
	echo Database is already backup, as $last
fi


TARGET=$TARGET/djmovies_images

if [ ! -d $TARGET ] ; then
	mkdir $TARGET
fi

rsync --delete -acvrz movies/static/mov_imgs/ $TARGET/


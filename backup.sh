#!/bin/bash

TARGET='/Volumes/ExtraX/Dropbox/backups'
DATABASE=db_movies.sqlite

cd `dirname $0`

next=1
for f in $TARGET/djmovies.*.sqlite ; do
	number=$(echo $f | grep -Eo '[1-9]\d*')
	let "number=1+$number"
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
	echo Database is already backup
fi


TARGET=$TARGET/djmovies_images

if [ ! -d $TARGET ] ; then
	mkdir $TARGET
fi

rsync --delete -acvrz movies/static/mov_imgs/ $TARGET/


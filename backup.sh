#!/bin/sh

cd `dirname $0`

tar cvfz ../djmovies.tgz db_movies.sqlite movies/static/mov_imgs

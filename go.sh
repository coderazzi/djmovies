#!/bin/bash
export MAGICK_HOME=/usr/local/Cellar/imagemagick@6/6.9.9-27/
cd `dirname $0`
./manage.py runserver

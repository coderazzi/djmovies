#!/bin/bash
#export MAGICK_HOME=/usr/local/Cellar/imagemagick@6/6.9.9-27/
#unalias python

cd `dirname $0`
source venv/bin/activate

if [ "$(uname -s)" = "Darwin" ] ; then
  open  "http://127.0.0.1:8000"
else
  xdg-open  "http://127.0.0.1:8000"
fi
python3 ./manage.py runserver

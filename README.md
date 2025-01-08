**DjMovies** is my personal movies organizer.

![snapshot](https://coderazzi.net/python/djmovies/djmovies.png)

# ABOUT

This is a django application that I started writing on April 1st 2013,
to handle my private catalog of movies.
In addition to catalog the movies, it exposes through its web interface
multiple tools to handle them: homogenize video and audio formats,
subtitles handling, etc.

DJMovies accesses external services, like IMDb to retrieve movie 
information, or Moviesubtitles.org to download subtitles.

Precisely this dependency on external services makes the project 
eternally unfinished. The access to the services scraps the information, 
but those services keep updating the appearance of their pages, 
requiring a regular update to the scraping process. 
Most of the changes implemented since 2014 relate exclusively to these updates.

As part of my process to stop using private repositories in my own VPSs, 
I am now making these repositories public. DJMovies is available from
https://github.com/coderazzi/djmovies, 
and the data associated to my own catalog lives in a separate private repository,
https://github.com/coderazzi/djmovies-userdata

I am quite astonished of the short time I have needed to migrate this 
application to the latest python version (3.13.1 as of today) and Django version (5.1.4), 
as I was using before Django 3.0.5. However, I have not tested the application in 
full, so additional changes will likely be required in the close future. 
Very specifically, the access to external services is likely not working now.


# Installation

## OS: install packages

### linux
	sudo apt-get install mediainfo unrar imagemagick libxml2-dev libxslt-dev zlib1g-dev ffmpeg mkvtoolnix  

### macos
	 brew install mediainfo rar freetype imagemagick@6 ffmpeg 
	 export MAGICK_HOME=/opt/homebrew/opt/imagemagick@6  

## Python setup

	 git clone https://github.com/coderazzi/djmovies    
	 cd djmovies  
	 python3 -m venv venv 
	 source venv/bin/activate 
	 pip3 install -r requirements.txt   

## Application initialization

I keep my data in a private repository, so I can initialize the application doing:

    git clone git@github.com:coderazzi/djmovies-userdata.git userdata 
    ln -sf ../../userdata/mov_imgs movies/static 

Otherwise, it is needed to setup the initial database

    mkdir -p userdata/mov_imgs
    sqlite3 userdata/db_movies.sqlite < db_schema
    ln -sf ../../userdata/mov_imgs movies/static 
    python3 ./manage.py migrate --fake

This userdata folder can then managed as a separate git repository

# Execution

	 ./go.sh

This will open a web page pointing out to http://127.0.0.1:8000
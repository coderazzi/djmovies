DjMovies is my personal movies organizer.

![snapshot](https://coderazzi.net/python/djmovies/djmovies.png)

# OS: install packages

## linux
	sudo apt-get install mediainfo unrar imagemagick libxml2-dev libxslt-dev zlib1g-dev ffmpeg mkvtoolnix  

## macos
	 brew install mediainfo rar freetype imagemagick@6 ffmpeg 
	 export MAGICK_HOME=/opt/homebrew/opt/imagemagick@6  

# Python setup

	 git clone https://github.com/coderazzi/djmovies    
	 cd djmovies  
	 python3 -m venv venv 
	 source venv/bin/activate 
	 pip3 install -r requirements.txt   

# Application initialization

I keep my data in a private repository, so I can initialize the application doing:

    git clone https://github.com/coderazzi/djmovies-userdata userdata 
    ln -sf ../../userdata/mov_imgs movies/static 

Otherwise, it is needed to setup the initial database

    mkdir -p userdata/mov_imgs
    sqlite3 userdata/db_movies.sqlite < db_schema
    ln -sf ../../userdata/mov_imgs movies/static 

Thus userdata folder can then managed as a separate git repository

# Run

	 ./go.sh

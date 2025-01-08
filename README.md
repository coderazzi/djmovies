DjMovies is my personal movies organizer.

# Install packages

## linux
	sudo apt-get install mediainfo unrar imagemagick libxml2-dev libxslt-dev zlib1g-dev ffmpeg mkvtoolnix  

## macos
	 brew install mediainfo rar freetype imagemagick@6 ffmpeg 
	 export MAGICK_HOME=/opt/homebrew/opt/imagemagick@6  

# Initial setup

	 git clone https://github.com/coderazzi/djmovies    
	 cd djmovies  
	 git clone https://github.com/coderazzi/djmovies-userdata userdata 
	 ln -sf ../../userdata/mov_imgs movies/static 
	 python3 -m venv venv 
	 source venv/bin/activate 
	 pip3 install -r requirements.txt   

To clear the database and start from scratch:

	bash userdata/clear_all.sh  


# Run

	 ./go.sh

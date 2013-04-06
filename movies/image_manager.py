# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

import os, re, stat

from django.db import models

from wand.image import Image as WandImage

class ImageManager(models.Manager):
    CONF_LAST_IMAGE_PATH='last image path'

    SIZE_BASIC='B'
    SIZE_LARGE='L'

    DIRECTORY_CHARS='abcdefghijklmnopqrstuvwxyz'
    DIRECTORY_BASE='movies/static/mov_imgs'
    FILE_ROOT_LEN=3
    MAX_FILES_PER_DIRECTORY=10**3
    FILE_ROOT_PATTERN='%%0%dd'%FILE_ROOT_LEN
    FILE_PATTERN=re.compile('\d'*FILE_ROOT_LEN)

    def create_basic_image(self, movieId, url, blob):
        return self.create_image(movieId, url, ImageManager.SIZE_BASIC, blob)

    def create_large_image(self, movieId, url, blob):
        return self.create_image(movieId, url, ImageManager.SIZE_LARGE, blob)

    def create_image(self, movieId, url, size, blob):
        from movies.models import Configuration, Lock

        def nextPath(path):
            if not path:
                ret=ImageManager.DIRECTORY_BASE
            else:
                ret=[]
                while path:
                    path, tail=os.path.split(path)
                    ret.insert(0, tail)
                length=len(ret)
                index=length-1
                while index>=0:
                    try:
                        i=ImageManager.DIRECTORY_CHARS.index(ret[index])
                    except:
                        break
                    if i<len(ImageManager.DIRECTORY_CHARS)-1:
                        ret[index]=ImageManager.DIRECTORY_CHARS[i+1]
                        length-=1
                        break
                    index-=1
                ret=os.path.join(*(ret[:index+1]+[ImageManager.DIRECTORY_CHARS[0]]*(length-index)))
            return ret

        def getNextAvailableFilename(lastPath):
            if lastPath:
                path, fileroot = os.path.split(lastPath)
                try: fileroot = int(fileroot)
                except: fileroot = 0
            else:
                path, fileroot = ImageManager.DIRECTORY_BASE, 0
            while True:
                try:    os.makedirs(path)
                except: pass
                listdir = set([int(base) for base in [each[:3] for each in os.listdir(path)] if ImageManager.FILE_PATTERN.match(base)])
                while fileroot < ImageManager.MAX_FILES_PER_DIRECTORY:
                    if fileroot not in listdir:
                        return os.path.join(path, ImageManager.FILE_ROOT_PATTERN%fileroot)
                    fileroot+=1
                path, fileroot = nextPath(path), 0

        path = Configuration.getValue(ImageManager.CONF_LAST_IMAGE_PATH)
        while True:            
            path = getNextAvailableFilename(path)
            if Lock.createLock(path):
                try:
                    #ensure that the path is still available
                    path_check=getNextAvailableFilename(path)
                    if path==path_check:
                        Configuration.setValue(ImageManager.CONF_LAST_IMAGE_PATH, path)
                        filename=path+os.path.splitext(url)[-1]
                        with open(filename, 'wb') as f:
                            f.write(blob)
                        try:
                            os.chmod(filename, stat.S_IREAD | stat.S_IRGRP)
                            with WandImage(filename=filename) as wi:
                                width, height = wi.size
                            return self.create(movie_id=movieId, url=url, path=filename, size=size, width=width, height=height)
                        except:
                            os.remove(filename)
                            raise
                    path=path_check
                finally:
                    Lock.removeLock(path)
        return ret

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

from wand.image import Image as WandImage

from django.db import models

from movies.logic.browser import Browser

class ImagesManager(models.Manager):
    CONF_LAST_IMAGE_PATH='last image path'

    DIRECTORY_CHARS='abcdefghijklmnopqrstuvwxyz'
    FILE_ROOT_LEN=3
    MAX_FILES_PER_DIRECTORY=10**3
    FILE_ROOT_PATTERN='%%0%dd'%FILE_ROOT_LEN
    FILE_PATTERN=re.compile('\d'*FILE_ROOT_LEN)

    def create(self, **kargs):
        if 'url' in kargs and 'path' not in kargs:
            kargs=kargs.copy()
            kargs.update(self._get_from_url(kargs['url'], kargs.get('size')))
        return super(ImagesManager, self).create(**kargs)

    def _get_from_url(self, url, size):
        from movies.models import Configuration, Lock, Image

        def nextPath(path):
            if not path:
                ret=Image.ABS_DIRECTORY_BASE
            else:
                ret=[]
                while path:
                    path, tail=os.path.split(path)
                    ret.insert(0, tail)
                length=len(ret)
                index=length-1
                while index>=0:
                    try:
                        i=ImagesManager.DIRECTORY_CHARS.index(ret[index])
                    except:
                        break
                    if i<len(ImagesManager.DIRECTORY_CHARS)-1:
                        ret[index]=ImagesManager.DIRECTORY_CHARS[i+1]
                        length-=1
                        break
                    index-=1
                ret=os.path.join(*(ret[:index+1]+[ImagesManager.DIRECTORY_CHARS[0]]*(length-index)))
            return ret

        def getNextAvailableFilename(lastPath):
            if lastPath:
                path, fileroot = os.path.split(lastPath)
                try: fileroot = int(fileroot)
                except: fileroot = 0
            else:
                path, fileroot = Image.ABS_DIRECTORY_BASE, 0
            while True:
                try:    os.makedirs(path)
                except: pass
                listdir = set([int(base) for base in [each[:3] for each in os.listdir(path)] if ImagesManager.FILE_PATTERN.match(base)])
                while fileroot < ImagesManager.MAX_FILES_PER_DIRECTORY:
                    if fileroot not in listdir:
                        return os.path.join(path, ImagesManager.FILE_ROOT_PATTERN%fileroot)
                    fileroot+=1
                path, fileroot = nextPath(path), 0

        def getUrl(url):
            with Browser() as browser:
                return browser.open_novisit(url).read()

        blob=getUrl(url)
        path = Configuration.getValue(ImagesManager.CONF_LAST_IMAGE_PATH)
        while True:            
            path = getNextAvailableFilename(path)
            if Lock.createLock(path):
                try:
                    #ensure that the path is still available
                    path_check=getNextAvailableFilename(path)
                    if path==path_check:
                        filename=path+os.path.splitext(url)[-1]
                        with open(filename, 'wb') as f:
                            f.write(blob)
                        try:
                            os.chmod(filename, stat.S_IREAD | stat.S_IRGRP)
                            with WandImage(filename=filename) as wi:
                                width, height = wi.size
                            if not size:
								if width<300: 
									size=Image.SIZE_BASIC 
								else: 
									size=Image.SIZE_LARGE
                            Configuration.setValue(ImagesManager.CONF_LAST_IMAGE_PATH, path)
                            rpath=os.path.relpath(filename, Image.ABS_DIRECTORY_BASE)
                            return {'path': rpath, 'size': size, 'width':width, 'height':height}
                        except:
                            os.remove(filename)
                            raise
                    path=path_check
                finally:
                    Lock.removeLock(path)        
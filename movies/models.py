# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

import os

from django.db import models, IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from movies.images_manager import ImagesManager

class Movie(models.Model):
    class Meta:
        db_table = 'movies'

    id = models.AutoField(primary_key=True)
    title = models.TextField(max_length=64)
    format = models.TextField(blank=True)
    year = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    imdb_duration = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    size = models.FloatField(null=True, blank=True)
    imdb_link = models.TextField(blank=True)
    trailer_link = models.TextField(blank=True)
    genres = models.TextField(blank=True)
    actors = models.TextField(blank=True)
    in_audios = models.TextField(blank=True)
    in_subs = models.TextField(blank=True)

    @property
    def subs(self):
        return self._languages(self.in_subs, [s.language for s in self.subtitle_set.all()])

    @property
    def embedded_subs(self):
        return self._languages(self.in_subs)

    @property
    def audios(self):
        return self._languages(self.in_audios)

    def _languages(self, a, base=None):
        ret, base, use = [], base or [], a or ''
        for each in ['English', 'Spanish', 'German', 'French', 'Portuguese', 'Latino']:
            if (each in use) or (each in base):
                ret.append(each)
        return (ret and (' / '.join(ret))) or ''

    def __unicode__(self):
        return "%s [%d]" % (self.title, self.id)


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)
    path = models.TextField(blank=True)
    movies = models.ManyToManyField(Movie, through='MoviePath')
    class Meta:
        db_table = 'locations'

    def __unicode__(self):
        return "%s [%d]" % (self.name, self.id)


class MoviePath(models.Model):
    movie = models.ForeignKey(Movie)
    location = models.ForeignKey(Location)
    path = models.TextField()
    class Meta:
        db_table = 'paths'


class Subtitle(models.Model):
    movie = models.ForeignKey(Movie)
    location = models.ForeignKey(Location)
    language = models.TextField()
    filename = models.TextField()
    class Meta:
        db_table = 'subtitles'


class Image(models.Model):
    objects = ImagesManager()
    id = models.AutoField(primary_key=True)
    movie = models.ForeignKey(Movie)
    url = models.TextField(blank=True)
    path = models.TextField(blank=True)
    size = models.TextField(blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = 'images'

    def __unicode__(self):
        movie = self.movie or '-no movie associated?-'
        return "%s [%dx%d]" % (movie, self.width, self.height)

    def abspath(self):
        return self.path and os.path.join(Image.ABS_DIRECTORY_BASE, self.path)

    def servepath(self):
        return self.path and os.path.join(Image.DIRECTORY_BASE, self.path)

    @staticmethod
    def delete_callback(**kwargs):
        try:
            os.remove(kwargs['instance'].abspath())
        except:
            pass

    SIZE_BASIC='B'
    SIZE_LARGE='L'
    DIRECTORY_BASE='static/mov_imgs'
    ABS_DIRECTORY_BASE=os.path.join('movies', DIRECTORY_BASE)


class Lock(models.Model):
    name = models.TextField(primary_key=True)
    class Meta:
        db_table = 'locks'

    def __unicode__(self):
        return self.name

    @staticmethod
    def createLock(name):
        try:
            Lock.objects.create(name=name)
            return True
        except IntegrityError:
            return False

    @staticmethod
    def removeLock(name):
        Lock.objects.filter(name=name).delete()


class Configuration(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.TextField(unique=True)
    value = models.TextField(blank=True)
    class Meta:
        db_table = 'configuration'

    def __unicode__(self):
        return self.key

    @staticmethod
    def getValue(key):
        try:
            return Configuration.objects.get(key=key).value
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def setValue(key, value):
        query = Configuration.objects.filter(key=key)
        if query:
            query.update(value=value)
        else:
            Configuration.objects.create(key=key, value=value)


#ensure now that images are properly deleted
models.signals.pre_delete.connect(Image.delete_callback, sender=Image, dispatch_uid="image.delete_callback")


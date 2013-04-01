# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

from django.db import models

class Movie(models.Model):
    id = models.IntegerField(primary_key=True)
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
    audios = models.TextField(blank=True)
    subs = models.TextField(blank=True)
    class Meta:
        db_table = 'movies'

    def __unicode__(self):
        return "%s [%d]" % (self.title, self.id)


class Location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)
    movies = models.ManyToManyField(Movie, through='MovieLocation')
    class Meta:
        db_table = 'locations'

    def __unicode__(self):
        return "%s [%d]" % (self.name, self.id)


class Configuration(models.Model):
    id = models.IntegerField(primary_key=True)
    key = models.TextField(unique=True)
    value = models.TextField(blank=True)
    class Meta:
        db_table = 'configuration'

    def __unicode__(self):
        return self.key


class Image(models.Model):
    id = models.IntegerField(primary_key=True)
    movie = models.ForeignKey(Movie)
    url = models.TextField(blank=True)
    path = models.TextField(blank=True)
    size = models.TextField(blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = 'images'

    def __unicode__(self):
        return "%s [%dx%d]" % (self.movie, self.width, self.height)


class MovieLocation(models.Model):
    movie = models.ForeignKey(Movie)
    location = models.ForeignKey(Location)
    path = models.TextField()
    class Meta:
        db_table = 'mmap'


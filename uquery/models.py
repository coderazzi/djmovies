from django.db import models

# Create your models here.

class UQuery(models.Model):


    id = models.AutoField(primary_key=True)
    title = models.TextField(unique=True)
    min_size = models.IntegerField(null=True, blank=True)
    last_check = models.IntegerField(null=True, blank=True)
    newest_result = models.IntegerField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'uqueries'


class UResults(models.Model):       

    oid = models.IntegerField()
    query = models.ForeignKey('UQuery')
    desc = models.TextField()
    size = models.IntegerField()
    nfo = models.TextField(null=True, blank=True)
    files = models.TextField()
    since = models.TextField()
    parts = models.IntegerField()
    total_parts = models.IntegerField()
    status = models.IntegerField()
    creation_time = models.IntegerField()

    class Meta:
        db_table = 'uresults'
        unique_together = (('oid', 'query'),)



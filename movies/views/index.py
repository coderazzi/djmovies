import random

from django.http import JsonResponse
from django.shortcuts import render

from movies.models import *


def index(request):
    locations = Location.objects.order_by('name')
    fmt = '%%-%ds - %%s' % max([len(l.name) for l in locations]) if locations else None
    print(Configuration.getValue(Configuration.IMDB_SEARCH_RESULTS) or 150)
    return render(request,
                  'index.html',
                  {'locations': locations,
                   'format': fmt,
                   'imdb_year1': Configuration.getValue(Configuration.IMDB_SEARCH_YEAR) or '',
                   'imdb_year2': Configuration.getValue(Configuration.IMDB_SEARCH_YEAR2) or '',
                   'imdb_results': Configuration.getValue(Configuration.IMDB_SEARCH_RESULTS) or 150,
                   })


def covers(request):
    ret = [(i.servepath(), i.width, i.height) for i in Image.objects.filter(size=Image.SIZE_BASIC)]
    random.shuffle(ret)
    return JsonResponse(dict(covers=ret))

import random

from django.http import JsonResponse
from django.template import RequestContext
from django.shortcuts import render_to_response

from movies.models import *



def index(request):
    locations=Location.objects.order_by('name')
    format='%%-%ds - %%s' % max([len(l.name) for l in locations]) if locations else None
    return render_to_response('index.html', 
        {'locations':  locations, 
         'format' : format,
         'imdb_year1': Configuration.getValue(Configuration.IMDB_SEARCH_YEAR) or '',
         'imdb_year2': Configuration.getValue(Configuration.IMDB_SEARCH_YEAR2) or '',
         'imdb_results': Configuration.getValue(Configuration.IMDB_SEARCH_RESULTS) or 150,
         },
        RequestContext(request))


def covers(request):
    covers=[(i.servepath(), i.width, i.height) for i in Image.objects.filter(size='B')]
    random.shuffle(covers)
    return JsonResponse(dict(covers=covers))    

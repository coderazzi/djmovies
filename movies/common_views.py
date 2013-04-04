import json

from django.core.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.template import Context, RequestContext, loader
from django.shortcuts import render_to_response, redirect

from movies.models import *

from local.locations import LocationHandler
from local.media import mediainfo
from local.imdb import getImdbInfo, getBasicImdbInfo, searchImdb



def index(request):
    movies=Movie.objects.order_by('title')[:9]
    images={}
    for each in movies:
        images=each.image_set.filter(size='B')[:1]
        if images:
            each.image=images[0].path
        
    context = Context({
        'movies': movies,
    })
    return render_to_response('movies.html', context)


def locations(request):        
    return render_to_response('locations.html', 
        {'locations':  Location.objects.order_by('name')},
        RequestContext(request))



import json

from django.core.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.template import Context, RequestContext, loader
from django.shortcuts import render_to_response, redirect

from movies.models import *



def index(request):        
    movies=Movie.objects.order_by('title')
    for movie in movies:
        images=movie.image_set.filter(size=Image.SIZE_BASIC)[:1]
        if images:
            movie.image=images[0].servepath()
        
    context = Context({
        'movies': movies,
    })
    return render_to_response('movies.html', context)

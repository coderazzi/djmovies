# import json

# from django.db import IntegrityError
# from django.contrib import messages
# from django.http import HttpResponse
from django.shortcuts import render_to_response#, redirect
from django.template import RequestContext

from movies.models import MoviePath#, Movie, Image, Subtitle

from movies.logic.locations import LocationHandler
from movies.logic.subtitles import SubtitleFileHandler

def show(request):    
    if request.method == 'GET': return redirect('#locations')

    subPath 	 = request.POST['subtitle.path']
    locationPath = request.POST['location.path']
    locationId   = request.POST['location.id']
    movieId      = request.POST['movie.id']

    locationHandler = LocationHandler(locationPath)
    moviePath=MoviePath.objects.get(location_id=locationId, movie_id=movieId).path

    fullpath = locationHandler.getSubtitlePath(moviePath, subPath)

    return render_to_response('subtitles_show.html', 
        {      
            'subHandler' : SubtitleFileHandler(fullpath),
            'error' : None,
            'times' : ['', '', '', '']
        },
        RequestContext(request))


def update(request):
    if request.method == 'GET': return redirect('#locations')

    times=[request.POST['t1f'], request.POST['t1t'], request.POST['t2f'], request.POST['t2t']]

    subHandler = SubtitleFileHandler(request.POST['path'])
    try:
        subHandler.shift(*times)
        times = ['', '', '', '']
        error=None
    except Exception, ex:
        error=str(ex)

    return render_to_response('subtitles_show.html', 
        {      
            'subHandler' : subHandler,
            'error' : error,
            'times' : times
        },
        RequestContext(request))

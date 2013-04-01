import json

from django.core.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.template import Context, RequestContext, loader
from django.shortcuts import render_to_response, redirect

from movies.models import *

from local.locations import LocationHandler
from local.media import mediainfo



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


def locations_add_path(request):    
    # if request.method == 'GET': return redirect('#locations')
    # locationId, locationPath = request.POST['location.id'], request.POST['location.path']
    if request.method == 'GET': 
        locationId, locationPath = 1, u'/Volumes/TTC7'
    else:
        locationId, locationPath = request.POST['location.id'], request.POST['location.path']


    movies= {}
    location = Location.objects.get(id=locationId)
    for each in MovieLocation.objects.filter(location=location):
        movies[each.path]=[each.movie.title, True]

    for path, ok in LocationHandler(locationPath).iterateAllFilesInPath():
        if ok:
            info = movies.get(path)
            if info:
                info[1]=False
            else:
                movies[path]=['', False]
        else:
            messages.warning(request, 'Cannot access path: '+path)
    
    info=[]
    for key in sorted(movies.keys(), key=unicode.lower):
        movie=movies[key]
        info.append((key, movie[0], movie[1]))

    return render_to_response('locations_add_path.html', 
        {      
            'location' : location,
            'path'     : locationPath,
            'movies'   : info,
        },
        RequestContext(request))



def locations_add_path_mediainfo(request):
    try:
        result = {'medianinfo' : mediainfo(request.POST['file.path'], request.POST['location.path']).__dict__}
    except Exception, ex:
        result = {'error': ex.message}
    import time
    time.sleep(1)
    return HttpResponse(json.dumps(result), content_type="application/json")
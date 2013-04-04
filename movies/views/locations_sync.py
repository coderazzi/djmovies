from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from movies.models import Location, MovieLocation

from local.locations import LocationHandler



def index(request):    
    # if request.method == 'GET': return redirect('#locations')
    # locationId, locationPath = request.POST['location.id'], request.POST['location.path']
    if request.method == 'GET': 
        locationId, locationPath = 1, u'/Volumes/TTC7/_movies'
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

    return render_to_response('locations_sync.html', 
        {      
            'location' : location,
            'path'     : locationPath,
            'movies'   : info,
        },
        RequestContext(request))
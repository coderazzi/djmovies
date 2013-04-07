import json
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from movies.models import Location, MovieLocation, Movie, Image

from local.locations import LocationHandler
from local.dstruct import Struct


def index(request):    
    if request.method == 'GET': return redirect('#locations')
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


def update(request):
    if request.method == 'GET': return redirect('#locations')
    data = json.loads(request.body)
    mediainfo, imdbinfo = Struct(**data['mediainfo']), Struct(**data['imdbinfo'])
    filepath, location= data['filepath'], data['location'], 

    locationHandler = LocationHandler(data['dirpath'])
    path = locationHandler.normalizeFilename(filepath, imdbinfo)
    try:
        movie = Movie.objects.create(title = imdbinfo.title,
                                    format=mediainfo.format, 
                                    year=imdbinfo.year,
                                    duration=mediainfo.duration,
                                    imdb_duration=imdbinfo.duration,
                                    width=mediainfo.width,
                                    height=mediainfo.height,
                                    size=mediainfo.size,
                                    imdb_link=imdbinfo.url,
                                    trailer_link=imdbinfo.trailer,
                                    genres=imdbinfo.genres,
                                    actors=imdbinfo.actors,
                                    audios=mediainfo.audios,
                                    subs=mediainfo.texts)
        try:
            if imdbinfo.imageLink:
                movie.image_set.create(url=imdbinfo.imageLink, size=Image.SIZE_BASIC)
            if imdbinfo.bigImageLink:
                movie.image_set.create(url=imdbinfo.bigImageLink, size=Image.SIZE_LARGE)
        except:
            movie.delete()
            raise
    except:
        locationHandler.reverseNormalization(filepath, path)
        raise

    # return render_to_response('locations_sync.html', 
    #     {      
    #         'location' : location,
    #         'path'     : dirpath,
    #         'movies'   : [],
    #     },
    #     RequestContext(request))

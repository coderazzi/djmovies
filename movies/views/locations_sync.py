import json

from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from movies.models import Location, MoviePath, Movie, Image

from local.locations import LocationHandler
from local.dstruct import Struct


def index(request):    
    if request.method == 'GET': return redirect('#locations')
    locationId, locationPath = request.POST['location.id'], request.POST['location.path']

    movies= {}
    location = Location.objects.get(id=locationId)
    for each in MoviePath.objects.filter(location=location):
        movies[each.path]=[each.movie.title, False, True] #title, in fs, in db

    problems=[]
    for path, error, type in LocationHandler(locationPath).iterateAllFilesInPath():
        if error:
            problems.append((0, path))
        else:
            if type==LocationHandler.SUBTITLE_FILE_IN_DIR:
                problems.append((2, path))
            elif type in [LocationHandler.UNVISITED_FOLDER, LocationHandler.UNHANDLED_FILE]:
                problems.append((1, path))
            else:
                info = movies.get(path)
                if info:
                    info[1]=True #in fs, okay
                else:
                    movies[path]=['', True, False] #in fs, not in db
    
    info=[]
    for key in sorted(movies.keys(), key=unicode.lower):
        movie=movies[key]
        info.append((key, movie[0], movie[1], movie[2]))

    problems.sort() 
    if problems and problems[0][0]==2:
        problems=[] #do not show at first info messages

    return render_to_response('locations_sync.html', 
        {      
            'location' : location,
            'path'     : locationPath,
            'movies'   : info, 
            'problems' : problems,
        },
        RequestContext(request))


def update(request):
    if not request.is_ajax(): return redirect('#locations')

    data = json.loads(request.body)
    mediainfo, imdbinfo = Struct.fromjs(**data['mediainfo']), Struct.fromjs(**data['imdbinfo'])
    filepath, locationId = data['filepath'], data['location']
    locationHandler = LocationHandler(data['dirpath'])
    path = locationHandler.normalizeFilename(filepath, imdbinfo)
    # for k, v in imdbinfo.__dict__.items():
    #     print k, v
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
                                    in_audios=mediainfo.audios,
                                    in_subs=mediainfo.texts)
        try:            
            if imdbinfo.imageLink:
                movie.image_set.create(url=imdbinfo.imageLink, size=Image.SIZE_BASIC)
            if imdbinfo.bigImageLink:
                movie.image_set.create(url=imdbinfo.bigImageLink, size=Image.SIZE_LARGE)
            try:
                MoviePath.objects.create(movie=movie, location_id=locationId, path=path)
            except IntegrityError:
                raise Exception('Movie (path) already exists on this location: repeated?')
        except:
            movie.delete()
            raise
    except Exception as ex:
        locationHandler.reverseNormalization(filepath, path)
        return HttpResponse(json.dumps({'error': 'Server error: '+str(ex)}), 
                            content_type="application/json")

    return render_to_response('locations_sync_item.html', 
        {      
            'in_fs'    : True,
            'in_db'    : True,
            'path'     : path,
            'title'    : imdbinfo.title,
        },
        RequestContext(request))

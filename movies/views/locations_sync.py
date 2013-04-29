import json

from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from movies.models import Location, MoviePath, Movie, Image, Subtitle

from local.locations import LocationHandler
from local.dstruct import Struct


def index(request):    
    if request.method == 'GET': return redirect('#locations')
    locationId, locationPath = request.POST['location.id'], request.POST['location.path']

    movies, subtitles = {}, {}
    location = Location.objects.get(id=locationId)
    for each in Subtitle.objects.filter(location_id=locationId):
        subtitles.setdefault(each.movie_id, []).append((each.filename, False, each.language))

    #we access the movies via the MoviePath table
    for each in MoviePath.objects.filter(location=location):
        #each.path is the full path, and each.movie the associated movie
        movies[each.path]=[each.path, each.movie.title, False, True, subtitles.get(each.movie_id, [])]

    #we will pass to the renderer a list of movies, sorted. Each is an array containing:
    #1-The path
    #2-The title
    #3-True if the movie exists in filesystem
    #4-True if the movie exists in database
    #5-Number of subtitles (added later)
    #6-list of subtitles. 
        #1- path (in same folder as movie)
        #2- true if the subtitle path exists in filesystem
        #3- language (None if not found in database)

    problems=[]
    for each in LocationHandler(locationPath).iterateAllFilesInPath():
        path, error, type, subs = each[0], each[1], each[2], (len(each)==3 and []) or each[3]
        if error:
            problems.append((0, path))
        elif type in [LocationHandler.UNVISITED_FOLDER, LocationHandler.UNHANDLED_FILE]:
            problems.append((1, path))
        else:
            info = movies.get(path)
            if info:
                info[2]=True #in fs, okay
                for subinfo in info[4]:
                    try:
                        subs.remove(info[0])
                        subinfo[2]=True
                    except ValueError:
                        pass
                for sub in subs:
                    info[4].append((sub, True, None))
            else:
                movies[path]=[path, '', True, False, [(sub, True, None) for sub in subs]] 
    
    info=[]
    for key in sorted(movies.keys(), key=unicode.lower):
        movie = movies[key]
        print movie
        subs = movie[4]
        movie[4] = max(1, len(subs))
        subs.sort(unicode.lower)
        movie.append(subs)
        info.append(movie)

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

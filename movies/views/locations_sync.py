import json

from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from movies.models import Location, MoviePath, Movie, Image, Subtitle

from local.imdb import getSubtitles
from local.locations import LocationHandler
from local.dstruct import Struct


DEBUGGING=False

LANGUAGES=['English', 'French', 'German', 'Portuguese', 'Spanish']
LANGUAGE_ABBRVS=['en', 'fr', 'de', 'pt', 'es'] #http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

def getLanguageAbbr(language):
    return LANGUAGE_ABBRVS[LANGUAGES.index(language)]

def getLanguage(languageAbbr):
    return LANGUAGES[LANGUAGE_ABBRVS.index(languageAbbr)]


def index(request):    
    if request.method == 'GET': return redirect('#locations')
    locationId, locationPath = request.POST['location.id'], request.POST['location.path']

    movies, subtitles = {}, {}
    location = Location.objects.get(id=locationId)
    for each in Subtitle.objects.filter(location_id=locationId):
        subtitles.setdefault(each.movie_id, []).append([each.filename, False, each.language])

    #we access the movies via the MoviePath table
    for each in MoviePath.objects.filter(location=location):
        #each.path is the full path, and each.movie the associated movie
        movies[each.path]=[each.path, each.movie.title, False, each.movie.id, each.movie.embedded_subs, subtitles.get(each.movie_id, [])]

    #we will pass to the renderer a list of movies, sorted. Each is an array containing:
    #1-The path
    #2-The title
    #3-True if the movie if the movie exists in filesystem
    #4-Id of the movie if the movie exists in database, 0 otherwise
    #5-Media subtitles (embedded)
    #6-Number of subtitles (added later)
    #7-list of subtitles. 
        #1- path (in same folder as movie)
        #2- true if the subtitle path exists in filesystem
        #3- language (None if not found in database)
    problems=[]
    for each in LocationHandler(locationPath).iterateAllFilesInPath():
        path, error, type, subs = each[0], each[1], each[2], (len(each)==4 and each[3]) or []
        if error:
            problems.append((0, path))
        elif type in [LocationHandler.UNVISITED_FOLDER, LocationHandler.UNHANDLED_FILE]:
            problems.append((1, path))
        else:
            info = movies.get(path)
            if info: #path, title, in_fs, movieId, subtitles
                info[2]=True #in fs, okay
                for subinfo in info[5]:
                    try:
                        subs.remove(subinfo[0])
                        subinfo[1]=True #in_fs
                    except ValueError:
                        pass
                for sub in subs:
                    info[5].append((sub, True, None))
            else:
                movies[path]=[path, '', True, 0, '', [(sub, True, None) for sub in subs]] 
    
    info=[]
    for key in sorted(movies.keys(), key=unicode.lower):
        movie = movies[key]
        subs = (movie[2] and movie[3] and movie[5]) or [] #do not include subtitles if not in file system or db
        movie[5] = 1 + len(subs)
        sorted(subs, key=(lambda x: unicode.lower(x[0])))
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
            'languages': LANGUAGES
        },
        RequestContext(request))


def edit_movie(request):
    '''
    adds information for a new movie or edits an existing one
    It returns the new TR element or elements to replace the existing one
    '''
    if not request.is_ajax(): return redirect('#locations')

    try:
        data            = json.loads(request.body)
        imdbinfo        = Struct.fromjs(**data['imdbinfo'])
        locationId      = data['location']
        filepath        = data['filepath']
        movieId         = int(data['movieId'])
        locationHandler = LocationHandler(data['dirpath'])
        oldMovie        = None

        if movieId:
            #we create the new movie information
            oldMovie  = Movie.objects.get(id=movieId)
            mediainfo = Struct( format=oldMovie.format,
                                duration=oldMovie.duration,
                                width=oldMovie.width,
                                height=oldMovie.height,
                                size=oldMovie.size,
                                audios=oldMovie.in_audios,
                                texts=oldMovie.in_subs)
        else:
            mediainfo = Struct.fromjs(**data['mediainfo'])

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

            #create now the correct MoviePath entry    
            path = locationHandler.normalizeFilename(filepath, imdbinfo)
            try:
                MoviePath.objects.create(movie=movie, location_id=locationId, path=path)
            except IntegrityError:
                locationHandler.reverseNormalization(filepath, path)
                raise Exception('Movie (path) already exists on this location: repeated?')
        except Exception as ex:
            movie.delete()
            raise

        currentSubtitles={}
        if oldMovie:
            for each in Subtitle.objects.filter(location_id=locationId, movie_id=movieId):
                lang=getLanguageAbbr(each.language)
                normalize = locationHandler.normalizeSubtitle(path, each.filename, lang)
                normalizedName = (normalize and normalize[0]) or each.filename
                each.movie_id = movie.id
                if normalize:
                    each.filename = normalize[0]
                each.save()
                currentSubtitles[each.filename] = each.language
            oldMovie.delete()

        subtitles = locationHandler.getSubtitles(path, currentSubtitles)

    except Exception as ex:
        return HttpResponse(json.dumps({'error': 'Server error: '+str(ex)}), 
                            content_type="application/json")


    return render_to_response('locations_sync_movie.html', 
        {      
            'in_fs'    : True,
            'db_id'    : movie.id,
            'path'     : path,
            'title'    : imdbinfo.title,
            'insubs'   : movie.embedded_subs, 
            'subs'     : subtitles,
            'lensubs'  : len(subtitles)+1,
            'languages': LANGUAGES
        },
        RequestContext(request))


def remove_movie(request):
    def handler(data):
        locationId, movieId = data['locationId'], data['movieId']
        Subtitle.objects.filter(location_id=locationId, movie_id=movieId).delete()
        MoviePath.objects.filter(movie_id=movieId, location_id=locationId).delete()
        if not MoviePath.objects.filter(movie_id=movieId):
            Movie.objects.filter(id=movieId).delete()
        
    return _handle_ajax_json(request, handler)

def remove_subtitle(request):
    def handler(data):
        locationId, movieId, path = data['locationId'], data['movieId'], data['path']
        Subtitle.objects.filter(location_id=locationId, movie_id=movieId, filename=path).delete()

    return _handle_ajax_json(request, handler)


def _handle_ajax_json(request, handler):
    if not request.is_ajax(): return redirect('#locations')

    handler(json.loads(request.body))

    return HttpResponse(json.dumps({'success': True}), content_type="application/json")


def edit_subtitle(request):

    if not request.is_ajax(): return redirect('#locations')
    error, renormalizeInfo = None, None
    try:
        data = request.POST
        locationId = data['location.id']
        movieId, subpath, language = data['movie.id'], data['file.path'], data['language']
        current = Subtitle.objects.filter(location_id=locationId, movie_id=movieId, filename=subpath)

        try:
            lang=getLanguageAbbr(language)
            try:
                moviePath=MoviePath.objects.get(location_id=locationId, movie_id=movieId).path
                try:
                    if data.get('normalize'):
                        locationHandler = LocationHandler(data['location.path'])
                        normalize = locationHandler.normalizeSubtitle(moviePath, subpath, lang)
                        if normalize: 
                            subpath, renormalizeInfo = normalize
                except Exception, ex:
                    if DEBUGGING: raise
                    error='Could not normalize subtitle: '+str(ex)
            except:
                if DEBUGGING: raise
                error='Database error: no such movie/location'
        except:
            if DEBUGGING: raise
            error='Invalid language: '+language
    except:
        if DEBUGGING: raise
        error='Invalid request'

    if not error:
        try:
            if current:
                subtitle=current[0]
                subtitle.filename=subpath
                subtitle.language=language
                subtitle.save()
            else: #add new subtile
                subtitle = Subtitle.objects.create(location_id=locationId, 
                    movie_id=movieId, 
                    language=language,
                    filename=subpath)
        except Exception as ex:
            if DEBUGGING: raise
            error = 'Server error: '+str(ex)

    if error: 
        if renormalizeInfo: locationHandler.renormalizeSubtitle(*renormalizeInfo)
        return HttpResponse(json.dumps({'error': error}), content_type="application/json")

    return render_to_response('locations_sync_subtitle.html', 
        {      
            'in_fs'    : True,
            'language' : language,
            'path'     : subpath
        },
        RequestContext(request))


def fetch_subtitles(request):
    if not request.is_ajax(): return redirect('#locations')
    data = request.POST
    movieId, locationId, language = data['movie.id'], data['location.id'], data['language']
    locationHandler = LocationHandler(data['location.path'])

    try:
        movie=Movie.objects.get(id=movieId)
        moviePath = MoviePath.objects.get(movie_id=movieId, location_id=locationId)
        subtitlesContent = getSubtitles(movie.title, movie.year, language)
        if not subtitlesContent:
            return HttpResponse(json.dumps({'error': 'No '+language+' subtitles found'}), content_type="application/json")    
        newPath, subtitles = locationHandler.storeSubtitles(moviePath.path, getLanguageAbbr(language),subtitlesContent)
    except Exception, ex:
        raise
        return HttpResponse(json.dumps({'error': str(ex)}), content_type="application/json")

    if newPath!=moviePath.path:
        moviePath.path=newPath
        moviePath.save()


    dbSubtitles = {}
    for each in Subtitle.objects.filter(location_id=locationId, movie_id=movieId):
        dbSubtitles[each.filename] = [each.filename, False, each.language]
    for each in subtitles:
        assoc = dbSubtitles.get(each)
        if assoc:
            assoc[1]=True
        else:
            dbSubtitles[each]=[each, True, None]
    subtitles=sorted(dbSubtitles.values(), key=(lambda x: unicode.lower(x[0])))

    return render_to_response('locations_sync_movie.html', 
        {      
            'in_fs'    : True,
            'db_id'    : movie.id,
            'path'     : newPath,
            'title'    : movie.title,
            'insubs'   : movie.embedded_subs, 
            'subs'     : subtitles,
            'lensubs'  : len(subtitles)+1,
            'languages': LANGUAGES
        },
        RequestContext(request))

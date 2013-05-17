import json

from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from movies.models import Location, MoviePath, Movie, Image, Subtitle

from local.imdb import getSubtitles, searchSubtitles
from local.locations import LocationHandler, SubtitleInfo
from local.dstruct import Struct


DEBUGGING=False

LANGUAGES=['English', 'French', 'German', 'Portuguese', 'Spanish']
LANGUAGE_ABBRVS=['en', 'fr', 'de', 'pt', 'es'] #http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes


class MovieSyncInfo:

    def __init__(self, path, movie=None, subtitlesInfo=None, in_fs=None):
        def get_image():
            if movie:
                ret=movie.image_set.order_by('size')[:1]
                return ret and ret[0].servepath()

        self.path  = path
        self.title = (movie and movie.title) or ''
        self.id = (movie and movie.id) or 0
        self.embedded_subs = movie and movie.embedded_subs
        self.audios = (movie and movie.audios) or ''
        self.exsubs = subtitlesInfo or []
        self.image = get_image()
        self.imdb_link= movie and movie.imdb_link
        if in_fs==None:
            self.in_fs = movie==None
        else:
            self.in_fs = in_fs

        #[each.path, each.movie.title, False, each.movie.id, each.movie.embedded_subs, subtitles.get(each.movie_id, [])]

    def getSubtitles(self):
        return (self.id and self.in_fs and self.exsubs) or []

    def getRowspan(self):
        return 1+len(self.getSubtitles())

    def setSubtitlesInPath(self, filenames):
        if self.title and self.title[0]=='4':
            print [e.filename for e in self.exsubs]
            print filenames
        self.in_fs=True
        for each in filenames:
            for st in self.exsubs:
                if st.filename==each:
                    st.in_fs=True
                    break
            else:
                self.exsubs.append(SubtitleInfo(filename=each))
        sorted(self.exsubs, key=(lambda x: unicode.lower(x.filename)))


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
        subtitles.setdefault(each.movie_id, []).append(SubtitleInfo(each.filename, each.language))

    #we access the movies via the MoviePath table
    for each in MoviePath.objects.filter(location=location):
        movies[each.path]=MovieSyncInfo(each.path, each.movie, subtitles.get(each.movie_id))

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
                info.setSubtitlesInPath(subs)
            else:
                movies[path]=MovieSyncInfo(path)
    
    info=[]
    for key in sorted(movies.keys(), key=unicode.lower):
        info.append(movies[key])

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
                print 'Creating ',movie.id, locationId, path
                MoviePath.objects.create(movie=movie, location_id=locationId, path=path)
            except IntegrityError:
                locationHandler.reverseNormalization(filepath, path)
                raise
                raise Exception('Movie (path) already exists on this location: repeated?')
        except Exception as ex:
            movie.delete()
            raise

        subtitles=[]
        if oldMovie:
            for each in Subtitle.objects.filter(location_id=locationId, movie_id=movieId):
                lang=getLanguageAbbr(each.language)
                normalize = locationHandler.normalizeSubtitle(path, each.filename, lang)
                normalizedName = (normalize and normalize[0]) or each.filename
                each.movie_id = movie.id
                if normalize:
                    each.filename = normalize[0]
                each.save()
                subtitles.append(SubtitleInfo(each.filename, each.language))
            oldMovie.delete()

        subtitles = locationHandler.syncSubtitleInfos(path, subtitles)

    except Exception as ex:
        return HttpResponse(json.dumps({'error': 'Server error: '+str(ex)}), 
                            content_type="application/json")


    return render_to_response('locations_sync_movie.html', 
        {      
            'movie'    : MovieSyncInfo(path, movie, subtitles, in_fs=True),
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
    handler(json.loads(request.body))

    return HttpResponse(json.dumps({'success': True}), content_type="application/json")


def trash_subtitle(request):
    data=json.loads(request.body)
    locationId, movieId, subpath = data['locationId'], data['movieId'], data['subpath']
    locationHandler = LocationHandler(data['locationPath'])
    moviePath=MoviePath.objects.get(location_id=locationId, movie_id=movieId).path
    if not locationHandler.removeSubtitle(moviePath, subpath):
        return HttpResponse(json.dumps({'error': 'Could not remove such file. Try a refresh'}), content_type="application/json")    

    Subtitle.objects.filter(location_id=locationId, movie_id=movieId, filename=subpath).delete()

    movie=Movie.objects.get(id=movieId)
    subtitles = locationHandler.syncSubtitleInfos(moviePath, [SubtitleInfo(each.filename, each.language) for each in Subtitle.objects.filter(location_id=locationId, movie_id=movieId)])
    return render_to_response('locations_sync_movie.html', 
        {      
            'movie'    : MovieSyncInfo(moviePath, movie, subtitles, in_fs=True),
            'languages': LANGUAGES
        },
        RequestContext(request))


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
            'sub' : SubtitleInfo(subpath, language, in_fs=True)
        },
        RequestContext(request))


def fetch_subtitles(request):
    if not request.is_ajax(): return redirect('#locations')
    data = request.POST
    movieId, locationId, language = data['movie.id'], data['location.id'], data['language']
    locationHandler = LocationHandler(data['location.path'])

    href = data.get('subtitle')
    if not href:
        #case A - just return the possible subtitles
        try:
            movie=Movie.objects.get(id=movieId)
            print searchSubtitles(movie.title)
            matches = sorted(searchSubtitles(movie.title), key=(lambda x: unicode.lower(x[0])))
            if not matches:
                return HttpResponse(json.dumps({'error': 'No such title found'}), content_type="application/json")    
        except Exception, ex:
            return HttpResponse(json.dumps({'error': str(ex)}), content_type="application/json")
        return render_to_response('locations_sync_subtitle_matches.html', 
            { 'subtitles'  : matches },
            RequestContext(request))

    #normal case - fetch the requested subtitle
    try:
        movie=Movie.objects.get(id=movieId)
        moviePath = MoviePath.objects.get(movie_id=movieId, location_id=locationId)
        subtitlesContent = getSubtitles(href, language)
        if not subtitlesContent:
            return HttpResponse(json.dumps({'error': 'No '+language+' subtitles found'}), content_type="application/json")    
        newPath, subtitles = locationHandler.storeSubtitles(moviePath.path, getLanguageAbbr(language), subtitlesContent)
    except Exception, ex:
        return HttpResponse(json.dumps({'error': str(ex)}), content_type="application/json")

    if newPath!=moviePath.path:
        moviePath.path=newPath
        moviePath.save()

    subtitles = locationHandler.syncSubtitleInfos(moviePath.path, [SubtitleInfo(each.filename, each.language) for each in Subtitle.objects.filter(location_id=locationId, movie_id=movieId)])

    return render_to_response('locations_sync_movie.html', 
        {      
            'movie'    : MovieSyncInfo(newPath, movie, subtitles, in_fs=True),
            'languages': LANGUAGES
        },
        RequestContext(request))



def get_movie_info(request):
    data =  json.loads(request.body)
    movieId, locationId = data['movieId'], data['locationId']
    locationHandler = LocationHandler(data['path'])

    movie=Movie.objects.get(id=movieId)
    moviePath = MoviePath.objects.get(movie_id=movieId, location_id=locationId).path
    subtitles = locationHandler.syncSubtitleInfos(moviePath, [SubtitleInfo(each.filename, each.language) for each in Subtitle.objects.filter(location_id=locationId, movie_id=movieId)])

    return render_to_response('locations_sync_movie.html', 
        {      
            'movie'    : MovieSyncInfo(moviePath, movie, subtitles, in_fs=True),
            'languages': LANGUAGES
        },
        RequestContext(request))

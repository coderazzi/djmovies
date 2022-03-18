import json, traceback

from django.http import HttpResponse

from movies.logic.media import mediainfo
from movies.logic.imdb import get_imdb_info, search_imdb



def _json_response(f):
    try:
        result = f()
    except Exception as ex:
        print(traceback.format_exc())
        result = {'error': 'Server error: '+str(ex)}
    return HttpResponse(json.dumps(result), content_type="application/json")


def get_mediainfo(request):
    def inner():
        ret = mediainfo(request.POST['file.path'], request.POST['location.path'])
        if ret:
            return {'mediainfo' : ret.__dict__}
        return {'error': 'Internal error using mediainfo'}
    return _json_response(inner)


def search_title(request):
    def inner():    
        references, first_info = search_imdb(request.POST['movie.title'])
        return {'links': references,
                'first_movie_info': first_info and first_info.__dict__}
    return _json_response(inner)


def access_url(request):
    def inner():
        info = get_imdb_info(request.POST['movie.imdb'])
        if info:
            return {'movie_info': info and info.__dict__}
        return {'error': 'Invalid IMDb reference'}
    return _json_response(inner)

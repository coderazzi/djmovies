import json

from django.http import HttpResponse

from local.media import mediainfo
from local.imdb import getImdbInfo, searchImdb



def _json_response(f):
    try:
        result = f()
    except Exception as ex:
        #raise
        result = {'error': 'Server error: '+str(ex)}
    #print json.dumps(result)
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
        references, firstInfo = searchImdb(request.POST['movie.title'].encode('ascii', 'ignore'))
        return {'links' : references, 
                'first_movie_info': firstInfo and firstInfo.__dict__}
    return _json_response(inner)


def access_url(request):
    def inner():
        info = getImdbInfo(request.POST['movie.imdb'])
        if info:
            return {'movie_info' : info and info.__dict__}
        return {'error': 'Invalid IMDb reference'}
    return _json_response(inner)

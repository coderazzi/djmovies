import json

from django.http import HttpResponse

from local.media import mediainfo
from local.imdb import getImdbInfo, searchImdb



SIMULATE=False
SIMULATE_TRY={'first_movie_info': {'bigImageLink': u'http://ia.media-imdb.com/images/M/MV5BMTYxOTAyNjEzNV5BMl5BanBnXkFtZTcwMTAxMDAwMQ@@._V1._SX320_SY475_.jpg', 'genres': u'Comedy/Drama', 'title': u'About Schmidt', 'url': u'http://www.imdb.com/title/tt0257360/?ref_=fn_al_tt_1', 'imageLink': u'http://ia.media-imdb.com/images/M/MV5BMTYxOTAyNjEzNV5BMl5BanBnXkFtZTcwMTAxMDAwMQ@@._V1_SX214_.jpg', 'actors': u'Jack Nicholson/Hope Davis/Dermot Mulroney', 'year': u'2002', 'duration': u'125', 'trailer': u'/video/screenplay/vi3820224793/?ref_=tt_ov_vi'}, 'links': [(u'http://www.imdb.com/title/tt0257360/?ref_=fn_al_tt_1', u'About Schmidt', u'(2002)'), (u'http://www.imdb.com/title/tt1418906/?ref_=fn_al_tt_2', u'Mortimer Hayden Smyth Talks About Gay Marriage', u'(2009) (Short)')]}
SIMULATE_INFO = {'movie_info': {'bigImageLink': None, 'genres': u'Short/Comedy', 'title': u'Mortimer Hayden Smyth Talks About Gay Marriage', 'url': u'http://www.imdb.com/title/tt1418906/?ref_=fn_al_tt_2', 'imageLink': None, 'actors': u'Connor Ratliff', 'year': u'2009', 'duration': u'7', 'trailer': None}}


def _json_response(f):
    try:
        result = f()
    except Exception, ex:
        result = {'error': 'Server error: '+ex.message}
    return HttpResponse(json.dumps(result), content_type="application/json")


def get_mediainfo(request):
    def inner():
        return {'mediainfo' : mediainfo(request.POST['file.path'], 
                                        request.POST['location.path']).__dict__}
    return _json_response(inner)


def search_title(request):
    def inner():
        if SIMULATE:
            # import time
            # time.sleep(2)
            return SIMULATE_TRY
        else:
            references, firstInfo = searchImdb(request.POST['movie.title'])
            return {'links' : references, 
                    'first_movie_info': firstInfo and firstInfo.__dict__}
    return _json_response(inner)


def access_url(request):
    def inner():
        if SIMULATE:
            # import time
            # time.sleep(2)
            result = SIMULATE_INFO.copy()
            result['url']=request.POST['movie.imdb']
            return result
        info = getImdbInfo(request.POST['movie.imdb'])
        if info:
            return {'movie_info' : info and info.__dict__}
        return {'error': 'Invalid IMDb reference'}
    return _json_response(inner)

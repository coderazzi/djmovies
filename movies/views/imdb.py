import json

from django.http import HttpResponse

from local.media import mediainfo
from local.imdb import getImdbInfo, getBasicImdbInfo, searchImdb



SIMULATE=False
SIMULATE_TRY={'first_movie_info': {'bigImageLink': u'http://ia.media-imdb.com/images/M/MV5BMTYxOTAyNjEzNV5BMl5BanBnXkFtZTcwMTAxMDAwMQ@@._V1._SX320_SY475_.jpg', 'genres': u'Comedy/Drama', 'title': u'About Schmidt', 'url': u'http://www.imdb.com/title/tt0257360/?ref_=fn_al_tt_1', 'imageLink': u'http://ia.media-imdb.com/images/M/MV5BMTYxOTAyNjEzNV5BMl5BanBnXkFtZTcwMTAxMDAwMQ@@._V1_SX214_.jpg', 'actors': u'Jack Nicholson/Hope Davis/Dermot Mulroney', 'year': u'2002', 'duration': u'125', 'trailer': u'/video/screenplay/vi3820224793/?ref_=tt_ov_vi'}, 'links': [(u'http://www.imdb.com/title/tt0257360/?ref_=fn_al_tt_1', u'About Schmidt', u'(2002)'), (u'http://www.imdb.com/title/tt1418906/?ref_=fn_al_tt_2', u'Mortimer Hayden Smyth Talks About Gay Marriage', u'(2009) (Short)')]}
SIMULATE_INFO = {'movie_info': {'bigImageLink': None, 'genres': u'Short/Comedy', 'title': u'Mortimer Hayden Smyth Talks About Gay Marriage', 'url': u'http://www.imdb.com/title/tt1418906/?ref_=fn_al_tt_2', 'imageLink': None, 'actors': u'Connor Ratliff', 'year': u'2009', 'duration': u'7', 'trailer': None}}

def get_mediainfo(request):
    try:
        # import time
        # time.sleep(2)
        result = {'mediainfo' : mediainfo(request.POST['file.path'], request.POST['location.path']).__dict__}
    except Exception, ex:
        result = {'error': ex.message}
    return HttpResponse(json.dumps(result), content_type="application/json")


def search_title(request):
    #return list of refernces as [(url, title, info)], plus the basic information on the first title
    try:
        if SIMULATE:
            # import time
            # time.sleep(2)
            result = SIMULATE_TRY
        else:
            references, firstInfo = searchImdb(request.POST['movie.title'])
            result = {'links' : references, 'first_movie_info': firstInfo and firstInfo.__dict__}
            print result
    except Exception, ex:
        result = {'error': ex.message}
    return HttpResponse(json.dumps(result), content_type="application/json")


def access_url(request):
    try:
        if SIMULATE:
            # import time
            # time.sleep(2)
            result = SIMULATE_INFO.copy()
            result['url']=request.POST['movie.imdb']
        else:
            info = getBasicImdbInfo(request.POST['movie.imdb'])
            result = {'movie_info' : info and info.__dict__}
            print result
    except Exception, ex:
        result = {'error': ex.message}
    return HttpResponse(json.dumps(result), content_type="application/json")

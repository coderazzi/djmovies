import json

from django.http import HttpResponse

from local.media import mediainfo
from local.imdb import getImdbInfo, searchImdb



SIMULATE=True
SIMULATE_TRY={'first_movie_info': {'bigImageLink': u'http://ia.media-imdb.com/images/M/MV5BMjA0OTU2MzYwOV5BMl5BanBnXkFtZTYwNTA3OTk5._V1._SX335_SY475_.jpg', 'genres': u'Comedy/Romance', 'title': u"There's Something About Mary", 'url': u'http://www.imdb.com/title/tt0129387/?ref_=fn_al_tt_1', 'imageLink': u'http://ia.media-imdb.com/images/M/MV5BMjA0OTU2MzYwOV5BMl5BanBnXkFtZTYwNTA3OTk5._V1_SY317_CR5,0,214,317_.jpg', 'actors': u'Ben Stiller/Cameron Diaz/Matt Dillon', 'year': u'1998', 'duration': u'119', 'trailer': u'/video/screenplay/vi3640000793/?ref_=tt_ov_vi'}, 'links': [(u'http://www.imdb.com/title/tt0129387/?ref_=fn_al_tt_1', u"There's Something About Mary", u'(1998)'), (u'http://www.imdb.com/title/tt1178610/?ref_=fn_al_tt_2', u"There's Something About Mary", u'(2007) (Video)'), (u'http://www.imdb.com/title/tt2503212/?ref_=fn_al_tt_3', u"There's Something About Mary", u'(2012) (TV Episode)'), (u'http://www.imdb.com/title/tt0798641/?ref_=fn_al_tt_4', u"There's Something About Mary", u'(2002) (TV Episode)'), (u'http://www.imdb.com/title/tt2628102/?ref_=fn_al_tt_5', u"There's Something About Mary", u'(2013) (TV Episode)'), (u'http://www.imdb.com/title/tt0909367/?ref_=fn_al_tt_6', u"There's Something About Mary", u'(2006) (TV Episode)'), (u'http://www.imdb.com/title/tt0685014/?ref_=fn_al_tt_7', u"There's Something About Mary", u'(2002) (TV Episode)'), (u'http://www.imdb.com/title/tt0825100/?ref_=fn_al_tt_8', u"There's Something About Mary", u'(2006) (TV Episode)'), (u'http://www.imdb.com/title/tt1175864/?ref_=fn_al_tt_9', u"There's Something About Mary O'Connor", u'(2008) (TV Episode)'), (u'http://www.imdb.com/title/tt1979615/?ref_=fn_al_tt_10', u"There's Something About Mary", u'(TV Episode)')]}
SIMULATE_INFO = {'movie_info': {'bigImageLink': None, 'genres': u'Short/Comedy', 'title': u'Mortimer Hayden Smyth Talks About Gay Marriage', 'url': u'http://www.imdb.com/title/tt1418906/?ref_=fn_al_tt_2', 'imageLink': None, 'actors': u'Connor Ratliff', 'year': u'2009', 'duration': u'7', 'trailer': None}}


def _json_response(f):
    try:
        result = f()
    except Exception as ex:
        result = {'error': 'Server error: '+str(ex)}
    print result
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

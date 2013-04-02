import json

from django.core.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.template import Context, RequestContext, loader
from django.shortcuts import render_to_response, redirect

from movies.models import *

from local.locations import LocationHandler
from local.media import mediainfo
from local.imdb import getImdbInfo, getBasicImdbInfo, getImdbReferences



def index(request):
    movies=Movie.objects.order_by('title')[:9]
    images={}
    for each in movies:
        images=each.image_set.filter(size='B')[:1]
        if images:
            each.image=images[0].path
        
    context = Context({
        'movies': movies,
    })
    return render_to_response('movies.html', context)


def locations(request):        
    return render_to_response('locations.html', 
        {'locations':  Location.objects.order_by('name')},
        RequestContext(request))


def locations_add_path(request):    
    # if request.method == 'GET': return redirect('#locations')
    # locationId, locationPath = request.POST['location.id'], request.POST['location.path']
    if request.method == 'GET': 
        locationId, locationPath = 1, u'/Volumes/TTC7/_movies'
    else:
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

    return render_to_response('locations_add_path.html', 
        {      
            'location' : location,
            'path'     : locationPath,
            'movies'   : info,
        },
        RequestContext(request))



def locations_add_path_mediainfo(request):
    try:
        result = {'mediainfo' : mediainfo(request.POST['file.path'], request.POST['location.path']).__dict__}
    except Exception, ex:
        result = {'error': ex.message}
    return HttpResponse(json.dumps(result), content_type="application/json")


def locations_add_path_imdbinfo_try(request):
    try:
        links=[(u'http://www.imdb.com/title/tt0147800/?ref_=fn_al_tt_1', u'10 Things I Hate About You', u'(1999)'), (u'http://www.imdb.com/title/tt1321805/?ref_=fn_al_tt_2', u'10 Things I Hate About You', u'(2009) (TV Series)'), (u'http://www.imdb.com/title/tt2402917/?ref_=fn_al_tt_3', u'10 Things I Hate About Life', u'(2013)'), (u'http://www.imdb.com/title/tt1816433/?ref_=fn_al_tt_4', u'10 Things I Hate About Camping', u'(2011) (Short)'), (u'http://www.imdb.com/title/tt0418437/?ref_=fn_al_tt_5', u'Things I Hate About You', u'(2004) (TV Series)'), (u'http://www.imdb.com/title/tt0386734/?ref_=fn_al_tt_6', u'Queer Things I Hate About You', u'(2001) (Short)'), (u'http://www.imdb.com/title/tt0545362/?ref_=fn_al_tt_7', u'Teen Things I Hate About You', u'(2005) (TV Episode)'), (u'http://www.imdb.com/title/tt1747465/?ref_=fn_al_tt_8', u'10 Things I Hate About You', u'(2007) (TV Episode)'), (u'http://www.imdb.com/title/tt1752304/?ref_=fn_al_tt_9', u'10 Things I Hate About You', u'(2010) (TV Episode)')]
        result = {'links' : links}
        # result = {'links' : getImdbReferences(request.POST['movie.title'])}
        # print result
    except Exception, ex:
        result = {'error': ex.message}
    return HttpResponse(json.dumps(result), content_type="application/json")

def locations_add_path_imdbinfo_exact(request):
    try:
        info = {'bigImageLink': u'http://ia.media-imdb.com/images/M/MV5BMTI4MzU5OTc2MF5BMl5BanBnXkFtZTYwNzQxMjc5._V1._SX334_SY475_.jpg', 'genres': u'Comedy/Drama/Romance', 'title': u'10 Things I Hate About You', 'imageLink': u'http://ia.media-imdb.com/images/M/MV5BMTI4MzU5OTc2MF5BMl5BanBnXkFtZTYwNzQxMjc5._V1_SY317_CR4,0,214,317_.jpg', 'actors': u'Heath Ledger/Julia Stiles/Joseph Gordon-Levitt', 'year': u'1999', 'duration': u'97', 'trailer': u'/video/screenplay/vi32480537/?ref_=tt_ov_vi'}
        info['url']=request.POST['movie.imdb']
        result = {'info' : info}
        # info = getBasicImdbInfo(request.POST['movie.imdb'])
        # result = {'info' : info and info.__dict__}
        # print result
    except Exception, ex:
        result = {'error': ex.message}
    return HttpResponse(json.dumps(result), content_type="application/json")

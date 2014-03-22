from django.template import Context
from django.shortcuts import render_to_response

from movies.models import *

from local.imdb import searchYear

def imdb(request, year, limit=150):    
    all= set([m[0] for m in Movie.objects.values_list('imdb_link')])
    context = Context({
        'year' : year,
        'search': filter(lambda s : s[0] not in all, searchYear(year, int(limit))),
    })
    return render_to_response('imdb_year_search.html', context)

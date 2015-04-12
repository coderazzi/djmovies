from django.template import Context
from django.shortcuts import render_to_response

from movies.models import *

from movies.logic.imdb import searchYear


def imdb(request, year, year2=None, limit=150):    
    if year2 is None:
        year2 = year
    else:
        if int(year2) < int(year):
            year, year2 = year2, year
    yearTitle = year if year==year2 else '%s-%s' % (year, year2)

    Configuration.setValue(Configuration.IMDB_SEARCH_YEAR, year)
    Configuration.setValue(Configuration.IMDB_SEARCH_YEAR2, year2)
    Configuration.setValue(Configuration.IMDB_SEARCH_RESULTS, limit)
    
    all= set([m[0] for m in Movie.objects.values_list('imdb_link')])
    context = Context({
        'year' : yearTitle,
        'limit': limit,
        'search': filter(lambda s : s[0] not in all, searchYear(year, year2, int(limit))),
    })
    return render_to_response('imdb_year_search.html', context)

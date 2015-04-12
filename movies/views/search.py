from django.template import Context
from django.shortcuts import render_to_response

from movies.models import *

from movies.logic.imdb import searchYear
from movies.logic.uquery_logic import standarize_title


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

    imdb_results = searchYear(year, year2, int(limit))    
    movies_in_database= set([m[0] for m in Movie.objects.values_list('imdb_link')])
    movies_in_uquery= set([m[0] for m in UQuery.objects.values_list('standarized_title')])

    results_to_show = filter(lambda s : s[0] not in movies_in_database, imdb_results)
    results_to_show = filter(lambda s : standarize_title(s[8]) not in movies_in_uquery, results_to_show)

    context = Context({
        'year' : yearTitle,
        'limit': limit,
        'search': results_to_show,
        'imdb_year1': Configuration.getValue(Configuration.IMDB_SEARCH_YEAR) or '',
        'imdb_year2': Configuration.getValue(Configuration.IMDB_SEARCH_YEAR2) or '',
        'imdb_results': Configuration.getValue(Configuration.IMDB_SEARCH_RESULTS) or 150,
    })
    return render_to_response('imdb_year_search.html', context)

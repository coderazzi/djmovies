from django.template import Context
from django.shortcuts import render_to_response

from movies.models import *

def index(request):    
    table, images = {}, {}
    for image in Image.objects.filter(size=Image.SIZE_BASIC):
        images[image.movie_id]=image.servepath()

    for movie in Movie.objects.order_by('title'):
        movie.image = images.get(movie.id)
        imdb_link=movie.imdb_link
        key = (movie.title, movie.year, imdb_link)
        locations=[(each.location, each.path) for each in movie.movielocation_set.all()]
        table.setdefault(key, []).append((movie, locations))

    keys = table.keys()
    keys.sort()

    context = Context({
        'info': [(k, table.get(k)) for k in keys],
    })
    return render_to_response('movies_control.html', context)



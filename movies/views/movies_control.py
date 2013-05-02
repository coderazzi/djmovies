from django.template import Context
from django.shortcuts import render_to_response

from movies.models import *

def index(request):    
    table, images = {}, {}

    for image in Image.objects.filter(size=Image.SIZE_BASIC):
        images[image.movie_id]=image.servepath()

    for movie in Movie.objects.order_by('title')[:20]:
        imdb_link=movie.imdb_link
        key = (movie.title, movie.year, imdb_link)
        locations=[(each.location, each.path) for each in movie.moviepath_set.all()]
        table.setdefault(key, []).append((movie, locations))

    info, keys = [], table.keys()
    keys.sort()
    for k in keys:
        image, mapped, cnt = None, table[k], 0
        for m, l in  mapped:
            if not image: image = images.get(m.id)
            cnt += max(1, len(l))
        info.append((k, image, cnt, [(m, l, max(1, len(l))) for m, l in mapped]))

    context = Context({
        'info': info,
    })
    return render_to_response('movies_control.html', context)

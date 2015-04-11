from django.template import Context
from django.shortcuts import render_to_response

from movies.models import *

def index(request):    
    info, images = [], {}

    for image in Image.objects.filter(size=Image.SIZE_BASIC):
        images[image.movie_id]=image.servepath()

    for movie in Movie.objects.order_by('title', 'year'):#[:12]:        
        locations=[(each.location, each.path) for each in movie.moviepath_set.all()]
        info.append((movie, images.get(movie.id), locations, 
            movie.genres.split('/') if movie.genres else [],
            movie.actors.split('/') if movie.actors else []
            ))

    print info

    context = Context({
        'info': info,
    })
    return render_to_response('movies_control.html', context)

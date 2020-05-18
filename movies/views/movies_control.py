from django.shortcuts import render

from movies.models import *


def index(request):
    info, images = [], {}

    for image in Image.objects.filter(size=Image.SIZE_BASIC):
        images[image.movie_id] = image.servepath()

    for movie in Movie.objects.order_by('title', 'year'):
        locations = [(each.location, each.path) for each in movie.moviepath_set.all()]
        info.append((movie, images.get(movie.id), locations,
                     movie.genres.split('/') if movie.genres else [],
                     movie.actors.split('/') if movie.actors else []
                     ))

    return render(request, 'movies_control.html', {'info': info,})

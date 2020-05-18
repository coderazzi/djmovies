from django.http import HttpResponse
from movies.models import Movie


def langs(request):
    movie_id, op = request.POST['movie.id'], request.POST['lang.target']

    ret = '/'.join([value for key, value in request.POST.items() if key.startswith('select.')])

    movie = Movie.objects.get(id=movie_id)

    if op == 'Audios':
        movie.in_audios = ret
        ret = movie.audios
    else:
        movie.in_subs = ret
        ret = movie.embedded_subs

    movie.save()

    return HttpResponse(ret)

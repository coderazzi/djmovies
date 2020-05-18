from django.shortcuts import render  # , redirect

from movies.models import MoviePath

from movies.logic.locations_handler import LocationHandler
from movies.logic.subtitles import SubtitleFileHandler


def show(request):
    if request.method == 'GET': return redirect('#locations')

    subPath = request.POST['subtitle.path']
    locationPath = request.POST['location.path']
    locationId = request.POST['location.id']
    movieId = request.POST['movie.id']

    locationHandler = LocationHandler(locationPath)
    moviePath = MoviePath.objects.get(location_id=locationId, movie_id=movieId).path

    fullpath = locationHandler.getSubtitlePath(moviePath, subPath)

    return render(request,
                  'subtitles_show.html',
                  {
                      'subHandler': SubtitleFileHandler(fullpath),
                      'error': None,
                      'times': ['', '', '', '']
                  })


def update(request):
    if request.method == 'GET': return redirect('#locations')

    times = [request.POST['t1f'], request.POST['t1t'], request.POST['t2f'], request.POST['t2t']]

    subHandler = SubtitleFileHandler(request.POST['path'])
    try:
        subHandler.shift(*times)
        times = ['', '', '', '']
        error = None
    except Exception as ex:
        error = str(ex)

    return render(request,
                  'subtitles_show.html',
                  {
                      'subHandler': subHandler,
                      'error': error,
                      'times': times
                  })

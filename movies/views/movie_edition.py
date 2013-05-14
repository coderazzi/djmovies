import json

from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from movies.models import Location, MoviePath, Movie, Image, Subtitle


def langs(request):

	movieId, op = request.POST['movie.id'], request.POST['lang.target']

	langs = '/'.join([value for key, value in request.POST.items() if key.startswith('select.')])

	movie=Movie.objects.get(id=movieId)

	if op=='Audios':
		movie.in_audios=langs
		ret=movie.audios
	else:
		movie.in_subs=langs
		ret=movie.embedded_subs

	movie.save()

	return HttpResponse(ret)



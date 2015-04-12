import json

from django.core.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.template import Context, RequestContext, loader
from django.shortcuts import render_to_response, redirect

from movies.models import *



def index(request):
    locations=Location.objects.order_by('name')
    format='%%-%ds - %%s' % max([len(l.name) for l in locations]) if locations else None
    return render_to_response('index.html', 
        {'locations':  locations, 'format' : format},
        RequestContext(request))

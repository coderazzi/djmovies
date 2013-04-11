from django.template import RequestContext
from django.shortcuts import render_to_response

from movies.models import Location


def index(request):        
    return render_to_response('locations.html', 
        {'locations':  Location.objects.order_by('name')},
        RequestContext(request))


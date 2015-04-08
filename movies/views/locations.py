from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.views.decorators.http import require_http_methods

from movies.models import Location

from django.contrib import messages

def index(request):        
    return render_to_response('locations.html', 
        {'locations':  Location.objects.order_by('name')},
        #{'locations':  []},
        RequestContext(request))


@require_http_methods(['POST'])
def update(request):        
    id, name, path = request.POST['location.id'], request.POST['location.name'], request.POST['location.path']
    if not name:
        error='The name cannot be empty'
    elif not path:
        error='The path cannot be empty'
    else:
        byname=Location.objects.filter(name=name)
        bypath=Location.objects.filter(path=path)
        if id:
            id=int(id)
            location=Location.objects.get(id=id)
        else:
            location=Location()
        if byname and (not id or byname[0].id!=id):
            error='The name of the location [%s] must be unique' % name
        elif bypath and (not id or bypath[0].id!=id):
            error='The path of the location [%s] must be unique: repeated for location [%s]' % (path, bypath[0].name)
        else:
            error=None
    if error:
        messages.add_message(request, messages.ERROR, error)
    else:
        location.name=name
        location.description=request.POST['location.description']
        location.path=path
        location.save()
    return redirect('#locations')

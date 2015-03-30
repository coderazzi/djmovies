from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.views.decorators.http import require_http_methods

import logic

def index(request):   
    return render_to_response('list.html',  {'queries':  logic.get_queries()}, RequestContext(request))


def query(request, query_id):
    use = logic.get_query(query_id)
    if use is None:
        return redirect(reverse('#uquery'))
    return render_to_response('query.html',  {'query':  use[0], 'results': use[1]}, RequestContext(request))


def query_base(request, query_id):
    use = logic.get_query(query_id)
    if use is None:
        return redirect(reverse('#uquery'))
    return render_to_response('query_base.html',  {'query':  use[0], 'results': use[1]}, RequestContext(request))


@require_http_methods(['POST'])
def requery_info(request):
    ret = logic.get_requery_info()
    if ret:
        return JsonResponse(dict(id=ret.id, title=ret.title))
    return JsonResponse(None, safe=False)


@require_http_methods(['POST'])
def create_query(request):
    query_exp  = request.POST.get('query')
    id, results = logic.create_query(query_exp)
    return JsonResponse(dict(query_id=id, results=results))


@require_http_methods(['POST'])
def refresh(request, query_id):
    minsize= request.POST.get('minsize')
    optimized= request.POST.get('optimized') is not None
    return JsonResponse(dict(new_results=logic.refresh_query(query_id, minsize, optimized)))


@require_http_methods(['POST'])
def query_completed(request, query_id):
    completed = request.POST.get('completed')=='true'
    return JsonResponse(dict(ok=bool(logic.query_completed(query_id, completed))))


@require_http_methods(['DELETE'])
def query_delete(request, query_id):
    return JsonResponse(dict(ok=bool(logic.query_delete(query_id))))


@require_http_methods(['POST'])
def update_result(request, query_id, oid):
    status   = request.POST.get('status')
    return JsonResponse(dict(ok=bool(logic.update_result_status(oid, query_id, status))))
            
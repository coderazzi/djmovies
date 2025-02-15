from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

import movies.logic.uquery_logic as logic


def index(request):
    return render(request, 'uquery.html', {'queries': logic.get_queries()})


def query(request, query_id):
    use = logic.get_query(query_id)
    if use is None:
        return redirect(reverse('#uquery'))
    return render(request, 'uquery_results_page.html', {'query': use[0], 'results': use[1]})


def query_base(request, query_id):
    use = logic.get_query(query_id)
    if use is None:
        return redirect(reverse('#uquery'))
    return render(request, 'uquery_results_content.html', {'query': use[0], 'results': use[1]})


@require_http_methods(['GET'])
def requery_info(request):
    ret = logic.get_requery_info()
    if ret:
        return JsonResponse(dict(id=ret.id, title=ret.title))
    return JsonResponse(None, safe=False)


def create_query(request):
    if request.method == 'GET':
        query_exp = request.GET.get('q')
        id, results = logic.create_query(query_exp)
        return redirect(reverse('#query', args=[id]))
    elif request.method == 'POST':
        query_exp = request.POST.get('query')
        id, results = logic.create_query(query_exp)
        return JsonResponse(dict(query_id=id, results=results))


@require_http_methods(['POST'])
def refresh(request, query_id):
    minsize = request.POST.get('minsize')
    optimized = request.POST.get('optimized') is not None
    return JsonResponse(dict(new_results=logic.refresh_query(query_id, minsize, optimized)))


@require_http_methods(['POST'])
def query_completed(request, query_id):
    completed = request.POST.get('completed') == 'true'
    return JsonResponse(dict(ok=bool(logic.query_completed(query_id, completed))))


@require_http_methods(['DELETE'])
def query_delete(request, query_id):
    return JsonResponse(dict(ok=bool(logic.query_delete(query_id))))


@require_http_methods(['POST'])
def update_result(request, query_id, oid):
    status = request.POST.get('status')
    return JsonResponse(dict(ok=bool(logic.update_result_status(oid, query_id, status))))

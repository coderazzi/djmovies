import re, time
from movies.models import UQuery, UResults
#from usenet_search_binsearch import search_title
from usenet_search_nzbindex import search_title

STATUS_NO_DOWNLOADED = 0xc0
STATUS_DOWNLOADED = 0xc1
STATUS_WRONG_RESULT = 0xcf

MIN_AGE_IN_SECONDS_TO_REQUERY = 86400 * 11  # 11 days
# MIN_AGE_IN_SECONDS_TO_REQUERY=500

DEFAULT_MIN_SIZE = 5800
DEFAULT_MAX_SIZE = 24000

# WORDS_SPLIT=re.compile('\w{3,}')
WORDS_SPLIT = re.compile('\w+')


def get_queries():
    return UQuery.objects.all().extra(
        select={'r_all': 'select count(*) from uresults where query_id=uqueries.id'}).extra(
        select={'r_valid': 'select count(*) from uresults where query_id=uqueries.id and status in (%s, %s)'},
        select_params=(STATUS_DOWNLOADED, STATUS_NO_DOWNLOADED))


def get_query(query_id):
    queries = UQuery.objects.filter(id=query_id)
    if not queries:
        return None
    query = queries[0]
    return query, _get_results(query_id, STATUS_WRONG_RESULT)


def get_requery_info():
    last_check = int(time.time()) - MIN_AGE_IN_SECONDS_TO_REQUERY
    ret = UQuery.objects.filter(completed=False, last_check__lt=last_check).order_by('last_check').only('id', 'title')[
          :1]
    return ret[0] if ret else None


def standarize_title(query_name):
    words = WORDS_SPLIT.findall(query_name.lower())
    return ' '.join(sorted(words))


def create_query(query_name):
    # if query already exists, we refresh it
    # if not, we create it.In both cases, we just return the query id
    stitle = standarize_title(query_name)
    query = UQuery.objects.filter(standarized_title=stitle)
    if query:
        query = query[0]
        results = _get_results(query.id)
        optimized = True
    else:
        query = UQuery(title=query_name, standarized_title=stitle, min_size=DEFAULT_MIN_SIZE)
        query.save()
        optimized, results = False, []
    return query.id, _update_results(query, results=results, only_get_newer_results=optimized)


def refresh_query(id, min_size, optimized):
    # Returns how many additional results has this query
    # if optimized is True, only new searches are treated
    queries = UQuery.objects.filter(id=id)
    if not queries:
        return None
    query = queries[0]
    if min_size is None:
        optimized = True
    else:
        min_size = int(min_size)
        if min_size != query.min_size:
            query.min_size = min_size
            query.save()
            optimized = False
    results = _get_results(query.id)
    return _update_results(query, results=results, only_get_newer_results=optimized)


def query_completed(id, completed):
    queries = UQuery.objects.filter(id=id)
    if queries:
        query = queries[0]
        query.completed = completed
        query.save()
        return True


def query_delete(id):
    queries = UQuery.objects.filter(id=id)
    if queries:
        queries.delete()
        return True


def update_result_status(oid, query_id, status):
    now = UResults.objects.filter(oid=oid, query_id=query_id)
    if now:
        result = now[0]
        result.status = status
        result.save()
        return True


def _get_results(query_id, exclude_status=5000):
    return UResults.objects.filter(query_id=query_id).exclude(status=exclude_status).extra(
        select={'ct_day': 'creation_time/86400'}).order_by('-ct_day', '-oid')


def _update_results(query, results=[], only_get_newer_results=True):
    newest_oid, new_results = search_title(query.standarized_title, query.min_size, DEFAULT_MAX_SIZE,
                                           exclude_oid_list=[d.oid for d in results],
                                           stop_on_oid=query.newest_result if only_get_newer_results else None)
    now = int(time.time())
    for d in reversed(new_results):
        UResults(query_id=query.id, oid=d.oid, desc=d.desc, size=d.size, nfo=d.nfo,
                 files=d.files, since=d.since, parts=d.parts, total_parts=d.total_parts,
                 status=STATUS_NO_DOWNLOADED, creation_time=now, download=d.download).save()
    query.last_check = now
    if newest_oid is not None:
        query.newest_result = newest_oid
    query.save()
    return len(new_results)

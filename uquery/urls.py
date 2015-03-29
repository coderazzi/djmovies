from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:sssss
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'uquery.views.index', name='#uquery'),

    url(r'^query$', 'uquery.views.create_query', name='#create_query'),    
    url(r'^query/(?P<query_id>\d+)$', 'uquery.views.query', name='#query'),
    url(r'^query/(?P<query_id>\d+)/base$', 'uquery.views.query_base', name='#query_base'),
    url(r'^query/(?P<query_id>\d+)/refresh$', 'uquery.views.refresh', name='#refresh'),
    url(r'^query/(?P<query_id>\d+)/set-completed$', 'uquery.views.query_completed', name='#query_completed'),
    url(r'^query/(?P<query_id>\d+)/delete$', 'uquery.views.query_delete', name='#query_delete'),

    url(r'^requery_info$', 'uquery.views.requery_info', name='#requery_info'),

    url(r'^result/(?P<query_id>\d+)/(?P<oid>\d+)/set-status$', 'uquery.views.update_result', name='#result_update'),
)


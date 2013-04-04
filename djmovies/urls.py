from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'movies.common_views.index', name='#index'),
    # url(r'^djmovies/', include('djmovies.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),


    url(r'^locations$', 'movies.common_views.locations', name='#locations'),
    url(r'^locations_sync$', 'movies.views.locations_sync.index', 
        name='#locations_sync'),

    url(r'^imdb_get_mediainfo$', 'movies.views.imdb.get_mediainfo', name='#imdb_get_mediainfo'),
    url(r'^imdb_search_title$', 'movies.views.imdb.search_title', name='#imdb_search_title'),
    url(r'^imdb_access_url$', 'movies.views.imdb.access_url', name='#imdb_access_url'),
)

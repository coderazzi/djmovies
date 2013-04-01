from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'movies.views.index', name='#index'),
    # url(r'^djmovies/', include('djmovies.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),


    url(r'^locations$', 'movies.views.locations', 
    	name='#locations'),
    url(r'^locations_add_path$', 'movies.views.locations_add_path', 
    	name='#locations_add_path'),
    url(r'^locations_add_path_mediainfo$', 'movies.views.locations_add_path_mediainfo', 
    	name='#locations_add_path_mediainfo'),
)

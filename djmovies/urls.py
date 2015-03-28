from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:sssss
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'movies.common_views.index', name='#index'),
    url(r'all$', 'movies.common_views.index', name='#index'),
    # url(r'^djmovies/', include('djmovies.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),

    url(r'^movies$', 'movies.views.movies_control.index', name='#movies'),



    url(r'^locations$', 'movies.views.locations.index', name='#locations'),
    url(r'^locations_sync$', 'movies.views.locations_sync.index', name='#locations_sync'),
    url(r'^subtitle_show$', 'movies.views.subtitles_bench.show', name='#subtitle_show'),
    url(r'^subtitle_update$', 'movies.views.subtitles_bench.update', name='#subtitle_update'),

    url(r'^imdb/(?P<year>\d{4})$', 'movies.views.search.imdb', name='#search'),
    url(r'^imdb/(?P<year>\d{4})-(?P<year2>\d{4})$', 'movies.views.search.imdb', name='#search'),
    url(r'^imdb/(?P<year>\d{4})/(?P<limit>\d{1,3})$', 'movies.views.search.imdb', name='#search'),
    url(r'^imdb/(?P<year>\d{4})-(?P<year2>\d{4})/(?P<limit>\d{1,3})$', 'movies.views.search.imdb', name='#search'),
    url(r'^ax_moved_langs$', 'movies.views.movie_edition.langs', name='#moved_langs'),

    url(r'^ax_lsync_edit$', 'movies.views.locations_sync.edit_movie', name='#locations_sync_edit'),
    url(r'^ax_lsync_remove$', 'movies.views.locations_sync.remove_movie', name='#locations_sync_remove'),
    url(r'^ax_lsync_info$', 'movies.views.locations_sync.get_movie_info', name='#locations_sync_info'),
    url(r'^ax_lsync_clean$', 'movies.views.locations_sync.clean_subtitles', name='#locations_sync_clean'),

    url(r'^ax_lsync_subtitle_fetch$', 'movies.views.locations_sync.fetch_subtitles', name='#lsync_subtitle_fetch'),
    url(r'^ax_lsync_subtitle_edit$', 'movies.views.locations_sync.edit_subtitle', name='#lsync_subtitle_edit'),
    url(r'^ax_lsync_subtitle_remove$', 'movies.views.locations_sync.remove_subtitle', name='#lsync_subtitle_remove'),
    url(r'^ax_lsync_subtitle_trash$', 'movies.views.locations_sync.trash_subtitle', name='#lsync_subtitle_trash'),

    url(r'^ax_imdb_get_mediainfo$', 'movies.views.dialog_imdb.get_mediainfo', name='#imdb_get_mediainfo'),
    url(r'^ax_imdb_search_title$', 'movies.views.dialog_imdb.search_title', name='#imdb_search_title'),
    url(r'^ax_imdb_access_url$', 'movies.views.dialog_imdb.access_url', name='#imdb_access_url'),
)

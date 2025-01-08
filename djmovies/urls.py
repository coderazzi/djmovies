from django.urls import re_path
from django.conf.urls.i18n import i18n_patterns

import movies.views.dialog_imdb
import movies.views.index
import movies.views.locations
import movies.views.locations_sync
import movies.views.movies_control
import movies.views.movie_edition
import movies.views.search
import movies.views.subtitles_bench
import movies.views.uquery

urlpatterns = [re_path(r'^$', movies.views.index.index, name='#index'),
               re_path(r'^ax_covers$', movies.views.index.covers, name='#covers'),

               re_path(r'^movies$', movies.views.movies_control.index, name='#movies'),

               re_path(r'^locations$', movies.views.locations.index, name='#locations'),
               re_path(r'^location/(?P<locationId>\d+)$', movies.views.locations_sync.index,
                   name='#locations_sync'),
               re_path(r'^locations_update$', movies.views.locations.update, name='#locations_update'),
               re_path(r'^subtitle_show$', movies.views.subtitles_bench.show, name='#subtitle_show'),
               re_path(r'^subtitle_update$', movies.views.subtitles_bench.update, name='#subtitle_update'),

               re_path(r'^imdb/(?P<year>\d{4})$', movies.views.search.imdb, name='#search'),
               re_path(r'^imdb/(?P<year>\d{4})-(?P<year2>\d{4})$', movies.views.search.imdb, name='#search'),
               re_path(r'^imdb/(?P<year>\d{4})/(?P<limit>\d{1,3})$', movies.views.search.imdb, name='#search'),
               re_path(r'^imdb/(?P<year>\d{4})-(?P<year2>\d{4})/(?P<limit>\d{1,3})$', movies.views.search.imdb,
                   name='#search'),
               re_path(r'^ax_moved_langs$', movies.views.movie_edition.langs, name='#moved_langs'),

               re_path(r'^ax_lsync_edit$', movies.views.locations_sync.edit_movie, name='#locations_sync_edit'),
               re_path(r'^ax_lsync_remove$', movies.views.locations_sync.remove_movie,
                   name='#locations_sync_remove'),
               re_path(r'^ax_lsync_info$', movies.views.locations_sync.get_movie_info,
                   name='#locations_sync_info'),
               re_path(r'^ax_lsync_clean$', movies.views.locations_sync.clean_subtitles,
                   name='#locations_sync_clean'),

               re_path(r'^ax_lsync_subtitle_fetch$', movies.views.locations_sync.fetch_subtitles,
                   name='#lsync_subtitle_fetch'),
               re_path(r'^ax_lsync_subtitle_edit$', movies.views.locations_sync.edit_subtitle,
                   name='#lsync_subtitle_edit'),
               re_path(r'^ax_lsync_subtitle_remove$', movies.views.locations_sync.remove_subtitle,
                   name='#lsync_subtitle_remove'),
               re_path(r'^ax_lsync_subtitle_trash$', movies.views.locations_sync.trash_subtitle,
                   name='#lsync_subtitle_trash'),

               re_path(r'^ax_imdb_get_mediainfo$', movies.views.dialog_imdb.get_mediainfo,
                   name='#imdb_get_mediainfo'),
               re_path(r'^ax_imdb_search_title$', movies.views.dialog_imdb.search_title,
                   name='#imdb_search_title'),
               re_path(r'^ax_imdb_access_url$', movies.views.dialog_imdb.access_url, name='#imdb_access_url'),

               re_path(r'^uquery$', movies.views.uquery.index, name='#uquery'),
               re_path(r'^uquery/$', movies.views.uquery.index, name='#uquery'),

               re_path(r'^uquery/query$', movies.views.uquery.create_query, name='#create_query'),
               re_path(r'^uquery/query/(?P<query_id>\d+)$', movies.views.uquery.query, name='#query'),
               re_path(r'^uquery/query/(?P<query_id>\d+)/base$', movies.views.uquery.query_base,
                   name='#query_base'),
               re_path(r'^uquery/query/(?P<query_id>\d+)/refresh$', movies.views.uquery.refresh, name='#refresh'),
               re_path(r'^uquery/query/(?P<query_id>\d+)/set-completed$', movies.views.uquery.query_completed,
                   name='#query_completed'),
               re_path(r'^uquery/query/(?P<query_id>\d+)/delete$', movies.views.uquery.query_delete,
                   name='#query_delete'),

               re_path(r'^uquery/requery_info$', movies.views.uquery.requery_info, name='#requery_info'),

               re_path(r'^uquery/result/(?P<query_id>\d+)/(?P<oid>\d+)/set-status$',
                   movies.views.uquery.update_result, name='#result_update'),
               ]

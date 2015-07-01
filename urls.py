from django.conf import settings

from django.conf.urls.defaults import patterns, url


# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'www.views.index', name='home'),

                       # admin
                       url(r'^admin/$', 'admin.views.index', name='admin'),
                       url(r'^admin/subject/(?P<subject_id>\d+)/', 'admin.views.subject', name='admin_subject'),
                       url(r'^admin/subject/', 'admin.views.subject', name='admin_subject'),
                       url(r'^admin/test_data/', 'admin.views.test_data'),

                       # auth
                       url(r'^auth/', 'auth.views.index'),

                       # api
                       url(r'api/daily/', 'api.views.daily'),
                       url(r'api/vote/', 'api.views.vote'),
                       url(r'api/subjects/user/([\w\d_-]{3,})/', 'api.views.subjects_for_user'),
                       url(r'api/subject/(?P<subject_id>\d{1,})/user/(?P<username>[\w\d_-]{3,})/',
                           'api.views.subject_for_user'),
                       url(r'api/subject/(?P<subject_id>\d{1,})/', 'api.views.subject_for_user', {'username': None}),
                       url(r'api/subjects/', 'api.views.subjects'),
                       url(r'api/current_photos/', 'api.views.photos'),
                       url(r'api/leaderboard/', 'api.views.leaderboard'),

                       url(r'api/instagram/', 'api.tasks.APICallWorker'),
                       )

if settings.LOCAL:
    urlpatterns += patterns('',
                            url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
                                {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                            )

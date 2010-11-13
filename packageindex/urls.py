from django.conf.urls.defaults import *

urlpatterns = patterns('packageindex.views',
    url(r'^$', 'application_list', name='packageindex.application_list'),
    url(r'^download/(?P<object_id>[\d]+)/$', 'download_package', name='packageindex.download_package'),
    url(r'^(?P<name>[\.\w\d-]+)/$', 'application_detail', name='packageindex.application_detail'),
)

from django.conf.urls.defaults import *

urlpatterns = patterns('packageindex.views',
    url(r'^p/$', 'application_list', name='packageindex.application_list'),
    url(r'^p/download/(?P<object_id>[\d]+)/$', 'download_package', name='packageindex.download_package'),
    url(r'^p/(?P<name>[\.\w\d-]+)/$', 'application_detail', name='packageindex.application_detail'),
    
    url(r'^(?P<access_key>[\w\d]+)/$', 'application_list', name='packageindex.keyed_application_list'),
    url(r'^(?P<access_key>[\w\d]+)/download/(?P<object_id>[\d]+)/$', 'download_package', name='packageindex.keyed_download_package'),
    url(r'^(?P<access_key>[\w\d]+)/(?P<name>[\.\w\d-]+)/$', 'application_detail', name='packageindex.keyed_application_detail'),
)

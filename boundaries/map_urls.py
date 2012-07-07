from django.conf.urls.defaults import patterns, include, url

from boundaries.views import *

urlpatterns = patterns('',
    url(r'^map/(?P<set_slug>[\w_-]+)/$', boundaries_map, name='boundaries_map'),
    url(r'^map/(?P<set_slug>[\w_-]+)/tiles$', boundaries_map_tiles, name='boundaries_map_tiles'),
)

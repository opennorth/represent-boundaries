from django.urls import path, re_path

from boundaries.views import (
    BoundaryDetailView,
    BoundaryGeoDetailView,
    BoundaryListView,
    BoundarySetDetailView,
    BoundarySetListView,
)

urlpatterns = [
    path(
        'boundary-sets/',
        BoundarySetListView.as_view(),
        name='boundaries_set_list'
    ),
    re_path(
        r'^boundary-sets/(?P<slug>[\w_-]+)/$',
        BoundarySetDetailView.as_view(),
        name='boundaries_set_detail'
    ),
    path(
        'boundaries/',
        BoundaryListView.as_view(),
        name='boundaries_boundary_list'
    ),
    re_path(
        r'^boundaries/(?P<geo_field>shape|simple_shape|centroid)$',
        BoundaryListView.as_view(),
        name='boundaries_boundary_list'
    ),
    re_path(
        r'^boundaries/(?P<set_slug>[\w_-]+)/$',
        BoundaryListView.as_view(),
        name='boundaries_boundary_list'
    ),
    re_path(
        r'^boundaries/(?P<set_slug>[\w_-]+)/(?P<geo_field>shape|simple_shape|centroid)$',
        BoundaryListView.as_view(),
        name='boundaries_boundary_list'
    ),
    re_path(
        r'^boundaries/(?P<set_slug>[\w_-]+)/(?P<slug>[\w_-]+)/$',
        BoundaryDetailView.as_view(),
        name='boundaries_boundary_detail'
    ),
    re_path(
        r'^boundaries/(?P<set_slug>[\w_-]+)/(?P<slug>[\w_-]+)/(?P<geo_field>shape|simple_shape|centroid)$',
        BoundaryGeoDetailView.as_view(),
        name='boundaries_boundary_detail'
    ),
]

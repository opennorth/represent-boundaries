from django.contrib.gis import admin

from boundaries.models import Boundary, BoundarySet


@admin.register(BoundarySet)
class BoundarySetAdmin(admin.ModelAdmin):
    list_filter = ('authority', 'domain')


@admin.register(Boundary)
class BoundaryAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'external_id', 'set')
    list_display_links = ('name', 'external_id')
    list_filter = ('set',)

import json
import sys

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from boundaries.models import BoundarySet


class Command(BaseCommand):
    help = _(
        'Create a report of the area of intersection of every pair of boundaries from two boundary sets '
        'specified by their slug.'
    )

    def add_arguments(self, parser):
        parser.add_argument('slug', nargs=2)
        parser.add_argument(
            '-f',
            '--format',
            action='store',
            dest='format',
            default='csv',
            help=_('Choose an output format: csv, json.'),
        )
        parser.add_argument(
            '-m',
            '--metadata',
            action='store_true',
            dest='include_metadata',
            default=False,
            help=_('Includes the original shapefile metadata in the output.'),
        )

    def handle(self, *args, **options):
        bset_a = BoundarySet.objects.get(slug=options['slug'][0])
        bset_b = BoundarySet.objects.get(slug=options['slug'][1])

        if options["format"] == "csv":
            print(bset_a.slug, "area_1", bset_b.slug, "area_2", "area_intersection", "pct_of_1", "pct_of_2")
        elif options["format"] == "json":
            output = []

        # For each boundary in the first set...
        for a_slug in bset_a.boundaries.order_by("slug").values_list('slug', flat=True):
            a_bdry = bset_a.boundaries.get(slug=a_slug)
            a_area = a_bdry.shape.area

            # Find each intersecting boundary in the second set...
            for b_bdry in bset_b.boundaries\
                    .filter(shape__intersects=a_bdry.shape):

                try:
                    geometry = a_bdry.shape.intersection(b_bdry.shape)
                except Exception as e:
                    sys.stderr.write(f"{a_slug}/{b_bdry.slug}: {e}\n")
                    continue

                int_area = geometry.area
                if geometry.empty:
                    continue

                b_area = b_bdry.shape.area

                # Skip overlaps that are less than .1% of the area of either of the shapes.
                # These are probably not true overlaps.
                if int_area / a_area < .001 or int_area / b_area < .001:
                    continue

                if options["format"] == "csv":
                    print(a_slug, a_area, b_bdry.slug, b_area, int_area, int_area / a_area, int_area / b_area)
                elif options["format"] == "json":
                    output.append({
                        "area": int_area,
                        bset_a.slug: {
                            "id": a_bdry.external_id,
                            "name": a_bdry.name,
                            "slug": a_slug,
                            "centroid": tuple(a_bdry.centroid),
                            "extent": a_bdry.extent,
                            "area": a_area,
                            "ratio": int_area / a_area,
                        },
                        bset_b.slug: {
                            "id": b_bdry.external_id,
                            "name": b_bdry.name,
                            "slug": b_bdry.slug,
                            "centroid": tuple(b_bdry.centroid),
                            "extent": b_bdry.extent,
                            "area": b_area,
                            "ratio": int_area / b_area,
                        },
                    })
                    if options["include_metadata"]:
                        output[-1][bset_a.slug]["metadata"] = a_bdry.metadata
                        output[-1][bset_b.slug]["metadata"] = b_bdry.metadata

        if options["format"] == "json":
            print(json.dumps(output, sort_keys=True, indent=2))

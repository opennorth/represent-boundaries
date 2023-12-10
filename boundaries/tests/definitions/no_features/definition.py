from datetime import date

import boundaries

boundaries.register(
    'Districts',
    last_updated=date(2000, 1, 1),
    name_func=boundaries.attr('id'),
    file='../../fixtures/foo.shp',
)

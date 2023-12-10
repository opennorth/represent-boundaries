from datetime import date

import boundaries

boundaries.register(
    'Polygons',
    last_updated=date(2000, 1, 1),
    name_func=boundaries.attr('str'),
)

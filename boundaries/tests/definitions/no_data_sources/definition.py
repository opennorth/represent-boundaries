from datetime import date

import boundaries

boundaries.register(
    'Empty',
    last_updated=date(2000, 1, 1),
    name_func=boundaries.attr('id'),
    file='../../fixtures/empty.zip',
)

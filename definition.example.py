from datetime import date

import boundaries

boundaries.register('Federal electoral districts',  # The string to be used for
    # the boundary set's slug. The slug will be "federal-electoral-districts".

    # (Optional) The path to the shapefile's directory relative to this file.
    # If this definition file and the shapefile share the same directory, you
    # can omit this parameter, or set it to the empty string.
    file='',
    # (Optional) The encoding of the shapefile's attributes. The default is
    # "ascii", but many shapefiles are encoded as "iso-8859-1".
    encoding='iso-8859-1',
    # (Optional) Override the Spatial Reference System Identifier (SRID) of
    # the shapefile.
    srid=4269,


    # The following Boundary Set fields will be made available via the API.

    # The most recent date on which the data was updated.
    last_updated=date(2011, 11, 28),
    # The plural name of the boundary set, for display. By default, it will use
    # the boundary set's slug.
    name='Federal electoral districts',
    # A generic singular name for a boundary in the set. If the boundary set's
    # name ends in "s", this parameter is optional, as is the case here.
    singular='Federal electoral district',

    # (Optional) The geographic area covered by the boundary set, which is
    # often a country, a region, a municipality, etc.
    domain='Canada',
    # (Optional) The entity responsible for publishing the data.
    authority='Her Majesty the Queen in Right of Canada',
    # (Optional) A URL to the source of the data.
    source_url='http://data.gc.ca/data/en/dataset/48f10fb9-78a2-43a9-92ab-354c28d30674',
    # (Optional) A URL to the licence under which the data is made available.
    licence_url='http://data.gc.ca/eng/open-government-licence-canada',
    # (Optional) The date from which the set's boundaries are in effect.
    start_date=None,
    # (Optional) The date until which the set's boundaries are in effect.
    end_date=None,
    # (Optional) Free-form text notes, often used to describe changes that were
    # made to the original source data, e.g. deleted or merged features.
    notes='',
    # (Optional) Any additional metadata to include in API responses.
    extra={'id': 'ocd-division/country:ca'},


    # The following Boundary functions take a feature as an argument and return
    # an appropriate value as described below.
    #
    # In this case, we use helper functions to access and clean attributes from
    # the shapefile:
    #
    # * `attr` retrieves a feature's attribute without making changes.
    # * `clean_attr` title-cases a string if it is all-caps, normalizes
    #   whitespace, and normalizes long dashes.
    # * `dashed_attr` does the same as `clean_attr`, but replaces all hyphens
    #   with long dashes.
    #
    # If you want to write your own function, set for example `name_func=namer`
    # and define a function that looks like:
    #
    # def namer(f):
    #   return f.get('FEDENAME')

    # A function that returns a feature's name.
    name_func=boundaries.clean_attr('FEDENAME'),

    # (Optional) A function that returns a feature's identifier, which should
    # be unique across the features in the shapefile and relatively stable
    # across time: for example, a district number or a geographic code. By
    # default, features have no identifiers.
    id_func=boundaries.attr('FEDUID'),
    # (Optional) A function that returns a feature's slug (the last part of its
    # URL path). By default, it will use the feature's name.
    slug_func=boundaries.attr('FEDUID'),
    # (Optional) A function that returns whether a feature should be loaded. By
    # default, all features are loaded.
    is_valid_func=lambda feature: True,
    # (Optional) A function that returns the Point at which to place a label
    # for the boundary, in EPSG:4326.
    label_point_func=lambda feature: None,
)

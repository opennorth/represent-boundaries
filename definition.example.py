from datetime import date

import boundaries

boundaries.register('federal-electoral-districts', # The slug of the boundary set

    # (Optional) The path to the shapefile's directory relative to this file. If
    # this definition file and the shapefile share the same directory, you can
    # omit this parameter, or set it to the empty string.
    file='',
    # (Optional)  The encoding of the shapefile's attributes. The default is
    # "ascii", but most shapefiles are encoded as "iso-8859-1".
    encoding='iso-8859-1',


    # The following Boundary Set fields will be made available via the API.

    # The name of the boundary set, for display.
    name='Federal electoral districts',
    # A generic singular name for a boundary in this set. If the boundary set's
    # name ends in "s", this parameter is optional, as is the case here.
    singular='Federal electoral district',
    # The date on which the data was most recently updated.
    last_updated=date(2011, 11, 28),

    # (Optional) A description of the boundary set's spatial coverage, which if
    # often a country, a region, a municipality, etc.
    domain='Canada',
    # (Optional) The authority publishing the data.
    authority='Her Majesty the Queen in Right of Canada',
    # (Optional) A URL to the source of the data.
    source_url='http://data.gc.ca/data/en/dataset/48f10fb9-78a2-43a9-92ab-354c28d30674',
    # (Optional) A URL to the licence for the data.
    licence_url='http://data.gc.ca/eng/open-government-licence-canada',
    # (Optional) Free-form text notes, often used to describe changes that were
    # made to the original source data: for example, deleted or merged features.
    notes='',
    # (Optional) Any additional metadata you would like to include in API responses.
    extra = { 'geographic_code': '01' },


    # The following Boundary functions take a feature as an argument and return
    # an appropriate value as described below.
    #
    # In this case, we are using helper functions to access and clean attributes
    # from the shapefile:
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

    # (Optional) A function that returns a feature's identifier, which should be
    # unique across the features in the shapefile and relatively stable across
    # time: for example, a district number or a geographic code. By default,
    # features have no identifiers.
    id_func=boundaries.attr('FEDUID'),
    # (Optional) A function that returns a feature's slug (the last part of its
    # URL path). By default, it will use the feature's name.
    slug_func=boundaries.attr('FEDUID'),
    # (Optional) A function that returns whether a feature should be loaded. By
    # default, all features are loaded.
    is_valid_func=lambda feature: True,
)

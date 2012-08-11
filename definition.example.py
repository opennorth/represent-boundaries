from datetime import date

import boundaries

boundaries.register('federal-electoral-districts', # The slug of the boundary set
	# The name of the boundary set for display.
	name='Federal electoral districts',
    # Generic singular name for a boundary from this set. Optional if the
    # boundary set's name ends in "s".
    singular='Federal electoral district', # If this were omitted, the same value would be generated
    # Geographic extents which the boundary set encompasses
    domain='Canada',
    # Path to the shapefile directory. Relative to the current file, so if this file
    # is in the same directory as the shapefile -- usually the case -- you can omit
    # this parameter.
    file='',
    # Last time the source was updated or checked for new data
    last_updated=date(1970, 1, 1),
    # A function that's passed the feature and should return a name string
    # The boundaries model provides some simple function factories for this.
    name_func=boundaries.clean_attr('FEDENAME'),
    # Function to extract a feature's "external_id" property
    id_func=boundaries.attr('FEDUID'),
    # Function to provide the slug (URL component) of the boundary
    # If not provided, uses the name to generate the slug; this is usually
    # what you want.
    #slug_func=boundaries.attr('FEDUID'),
    # Authority that is responsible for the accuracy of this data
    authority='H.R.M. Queen Elizabeth II',
    # A URL to the source of this data
    source_url='http://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/bound-limit-eng.cfm',
    # A URL to the license for this data
    licence_url='http://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/license-eng.cfm?lang=_e&year=11&type=fed000a&format=a',
    # A URL to the data file, e.g. a ZIP archive
    data_url='http://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/files-fichiers/gfed000a11a_e.zip',
    # Notes identifying any pecularities about the data, such as columns that
    # were deleted or files which were merged
    notes='',
    # Encoding of the text fields in the shapefile, e.g. 'utf-8'. Default: 'ascii'
    encoding='iso-8859-1',
    
    # For maps...
    
    # optional. A function from a feature object to a Point where to display a label for feature on a map.
    label_point_func = lambda feature : None,
    
    # Other utilities...
    
    # optional. A function from a feature object to a boolean indicating
    # whether it should be loaded into the database.
    #is_valid_func = lambda feature : True
)


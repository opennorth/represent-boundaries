# Represent API: Boundaries

[Represent](http://represent.opennorth.ca) is the open database of Canadian elected representatives and electoral districts. It provides a RESTful API to boundary, representative, and postcode resources.

This repository provides an API to geographic boundaries. It is based on the Chicago Tribune's [django-boundaryservice](http://github.com/newsapps/django-boundaryservice).

The [represent-canada](http://github.com/opennorth/represent-canada) repository provides a full sample app.

API documentation is available at [represent.opennorth.ca/api/](http://represent.opennorth.ca/api/#boundaryset).

## Installation

Install dependencies:

    pip install django-appconf django-jsonfield django-tastypie pycairo
    
(Only some utility classes are used from Tastypie. pycairo is used for maps only and is otherwise optional.)

Install the package:

    python setup.py install

Add `boundaries` to INSTALLED_APPS in your settings.py.

Add the following to your urls.py:

    (r'', include('boundaries.urls')),

Run `python manage.py syncdb` (or `migrate` if you use South).

## Adding data

By default, shapefiles are expected to be in subdirectories of [project_dir]/data/shapefiles, though this can be configured via the `BOUNDARIES_SHAPEFILES_DIR` setting.

To load data, run

    python manage.py loadshapefiles

This command loads every file for which it can find a definition. It looks for definitions in files ending with `definition.py` or `definitions.py` in `BOUNDARIES_SHAPEFILE_DIR` or its subdirectories.

See the sample definition in [definition.example.py](http://github.com/rhymeswithcycle/represent-boundaries/blob/master/definition.example.py).

Note that it's a good idea to keep DEBUG off during this process or Django will try to remember every SQL command.

## API starting point

The starting point for exploring the API resources is /boundary-sets. From there you'll see references to additional URLs to look at.

## Maps

This app can also generate colorful map layers for Google Maps API. When loading shapefiles, use the -c option to automatically compute colors for each boundary. This adds some extra processing time:

   python manage.py loadshapefiles -c
   
Because the maps are not cached within the app (that's your responsibility) and they require a significant amount of computer resources to generate, the map URLs are disabled by default. To enable, place in your urls.py:

   (r'', include('boundaries.map_urls')),
   
Then view a map example at:

   /map/[your-boundary-set-slug]/

## Contact

Please use [GitHub Issues](http://github.com/rhymeswithcycle/represent-boundaries/issues) for bug reports. You can also contact represent@opennorth.ca.
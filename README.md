# Represent Boundaries

This repository provides an API to geographic boundaries. It is based on the Chicago Tribune's [django-boundaryservice](http://github.com/newsapps/django-boundaryservice) from [this commit](https://github.com/newsapps/django-boundaryservice/commit/67e79d47d49eab444681309328dbe6554b953d69).

[Represent](http://represent.opennorth.ca) is an open database of Canadian elected representatives and electoral districts. It provides a RESTful API to boundary, representative, and postcode resources.

The [represent-canada](http://github.com/opennorth/represent-canada) repository provides a full sample app, and points to plugins which add representative, postcode, and map features to this boundaries API.

API documentation is available at [represent.opennorth.ca/api/](http://represent.opennorth.ca/api/#boundaryset).

## Installation

Install the package:

    pip install represent-boundaries

Add the following to `INSTALLED_APPS` in your `settings.py`:

    'boundaries',

Add the following to your `urls.py`:

    (r'', include('boundaries.urls')),

Run:

    python manage.py syncdb

## Adding data

Shapefiles are loaded from `BOUNDARIES_SHAPEFILES_DIR`, which defaults to `./data/shapefiles`. This directory contains a directory tree of shapefiles and definition files named `definition.py` or `definitions.py`. Definition files register "boundary sets," .

To load data, run:

    python manage.py loadshapefiles

This command loads every file for which it can find a definition.

See the sample definition in [definition.example.py](http://github.com/rhymeswithcycle/represent-boundaries/blob/master/definition.example.py).

Note that it's a good idea to keep `DEBUG` off during this process or Django will try to remember every SQL command.

## API starting point

The starting point for exploring the API resources is /boundary-sets. From there you'll see references to additional URLs to look at.

## Contact

Please use [GitHub Issues](http://github.com/opennorth/represent-canada/issues) for bug reports. You can also contact [represent@opennorth.ca](mailto:represent@opennorth.ca).

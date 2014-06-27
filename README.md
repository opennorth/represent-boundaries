# Represent Boundaries

Represent Boundaries is a web service allowing you to easily perform queries on geographic boundaries. For example:

* Submit a latitude and longitude to find the electoral district that contains it
* Render a map of school districts in your region
* Find boundaries that intersect or touch another boundary

Represent Boundaries provides a command-line tool to easily load shapefiles into the API. It's a Django app that's easy to integrate into your own project or to deploy on its own as an independent web service.

Notable deployments include:

* [Represent](http://represent.opennorth.ca) helps people find the elected officials and electoral districts for any Canadian address or postal code, at any level of government.
* [OpenStates.org](http://openstates.org/find_your_legislator/) allows anyone to discover more about lawmaking in their state and uses Represent Boundaries to help them find their state legislators.
* [GovTrack.us](https://www.govtrack.us/congress/members) helps track the activities of the United States Congress and uses Represent Boundaries to help people find their members of Congress.
* [ANCFinder.org](http://ancfinder.org/) helps Washington, DC residents discover and participate in their Advisory Neighborhood Commissions.

## Install

Represent Boundaries requires Python 2.7 or 3.3 and PostGIS. If you are unfamiliar with PostGIS and use OS X, install Xcode from the App Store, [install Homebrew](https://github.com/opennorth/opennorth.ca/wiki/Python-Quick-Start:-OS-X#homebrew), [install Python](https://github.com/opennorth/opennorth.ca/wiki/Python-Quick-Start:-OS-X#python-and-virtualenv) and [install PostGIS](https://github.com/opennorth/opennorth.ca/wiki/Python-Quick-Start:-OS-X#gdal-and-postgis). The last instructions to create a PostGIS template database are similar on Linux.

Now, create a PostGIS database using the template you created:

    createdb -h localhost my_database -T template_postgis

Install Represent Boundaries and, if you haven't already, Django and psycopg2, a PostgreSQL adapter:

    pip install represent-boundaries Django psycopg2

Start a new Django project (skip if you are integrating Represent Boundaries into an existing project):

    django-admin.py startproject my_project

In `my_project/settings.py`, [configure the default database](https://docs.djangoproject.com/en/dev/ref/contrib/gis/tutorial/#configure-settings-py) to connect to your PostGIS database and add `'boundaries'` to the list of `INSTALLED_APPS`.

In `my_project/urls.py`, add this line at the end of the `urlpatterns` list:

    (r'', include('boundaries.urls')),

From your project's directory, run:

    python manage.py syncdb --noinput

You can now run `python manage.py runserver` and navigate to `http://127.0.0.1:8000/boundary-sets/` to see your empty API. Let's add some data!

## Load shapefiles

[Shapefiles](http://en.wikipedia.org/wiki/Shapefile) are a popular geospatial vector data format for geographic information system (GIS) software, developed by ESRI. Other formats like KML, GeoJSON and others are easily converted to shapefile using tools like [`ogr2ogr`](http://www.gdal.org/ogr2ogr.html). A first step is to collect the geospatial data that you need.

Ready? Before continuing, in `my_project/settings.py`, change `DEBUG` to `False` to avoid high memory consumption.

Represent Boundaries looks for definition files, named `definition.py` or `definitions.py`, in `my_project/data/shapefiles` by default. Definition files describe how to load shapefiles into the API. When a shapefile is loaded, a **boundary set** is created for the shapefile and a **boundary** is created for each polygon feature in the shapefile. See the [example definition file](http://github.com/opennorth/represent-boundaries/blob/master/definition.example.py) for details on how to control how shapefiles are loaded. Most parameters in definition files are optional.

You can change the `data/shapefiles` path by setting `BOUNDARIES_SHAPEFILES_DIR` in `my_project/settings.py`. Represent Boundaries will walk the entire directory tree looking for definition files, so you may organize your shapefiles any way you like. [Some](https://github.com/sunlightlabs/pentagon/blob/master/shapefiles/definitions.py) put the shapefiles in subdirectories with a single top-level `definitions.py` file; [others](https://github.com/opennorth/represent-canada-data) create a directory tree with a `definition.py` file in each directory containing a shapefile.

Once you've written a definition for each shapefile, run:

    python manage.py loadshapefiles

The data should now be available via the API.

## Use the API

You can explore the API starting from `/boundary-sets/`. You'll see links to get details on each individual boundary set and links to browse each boundary set's boundaries. Add `?format=apibrowser` to the end of the URL to make it easier to click on links and explore the API. Once you find your way to the details of an individual boundary, you'll see links to get its shape, simplified shape, or centroid.

For all API documentation, including filters and geospatial queries, [read the API reference](http://represent.opennorth.ca/api/#boundaryset).

## What It Doesn't Do

Represent Boundaries doesn't support:

* Versioning of boundary sets or boundaries
* Hierarchies of boundary sets
* Points in addition to polygons

If you need those features, have a look at [MapIt](http://mapit.poplus.org/). That said, users have found workarounds, or have built small Django apps to fill in these gaps. For example, [Imago](https://github.com/opencivicdata/imago) introduces "temporal sets" to add dates to boundary sets. [Represent Postcodes](https://github.com/rhymeswithcycle/represent-postcodes) adds support for Canadian postal codes, which are points. Instead of versioning, most users namespace boundary sets with a year: for example, `federal-electoral-districts-2003` or `federal-electoral-districts-2013`.

If you would like to create colorful map tile layers, check out [Represent Maps](https://github.com/JoshData/represent-maps) by Joshua Tauberer.

## Acknowledgements

Represent Boundaries is based on the Chicago Tribune's [django-boundaryservice](http://github.com/newsapps/django-boundaryservice).

## Bugs? Questions?

This project's main repository is on GitHub: [http://github.com/opennorth/represent-boundaries](http://github.com/opennorth/represent-boundaries), where your contributions, forks, bug reports, feature requests, and feedback are greatly welcomed.

Released under the MIT license

Represent Boundaries
====================

|PyPI version| |Build Status| |Coverage Status|

Represent Boundaries is a web API to geographic areas, like electoral
districts. It allows you to easily find the areas that cover your users'
locations to display location-based information, like profiles of
electoral candidates.

It's a Django app that's easy to integrate into an existing project or
to deploy on its own. It uses a simple file format to control how data
is loaded into the API, and it provides a command-line tool to easily
manage data.

Notable uses include:

-  `Represent <https://represent.opennorth.ca/>`__ helps people find the
   elected officials and electoral districts for any Canadian address or
   postal code, at any level of government.
-  `OpenStates.org <http://openstates.org/find_your_legislator/>`__
   allows anyone to discover more about lawmaking in their state and
   uses Represent Boundaries to help them find their state legislators.
-  `GovTrack.us <https://www.govtrack.us/congress/members>`__ helps
   track the activities of the United States Congress and uses Represent
   Boundaries to help people find their members of Congress.
-  `ANCFinder.org <http://ancfinder.org/>`__ helps Washington, DC
   residents discover and participate in their Advisory Neighborhood
   Commissions.

Public instances include:

-  `represent.opennorth.ca <https://represent.opennorth.ca/>`__ for
   Canada: `source
   code <https://github.com/opennorth/represent-canada>`__ and `data
   files <https://github.com/opennorth/represent-canada-data>`__
-  `gis.govtrack.us <http://gis.govtrack.us/map/demo/cd-2012/>`__ for
   the US: `source code <https://github.com/JoshData/boundaries_us>`__

Documentation
-------------

-  `Installation <https://opennorth.github.io/represent-boundaries-docs/docs/install/>`__
-  `Add data to the API <https://opennorth.github.io/represent-boundaries-docs/docs/import/>`__
-  `Use the API <https://opennorth.github.io/represent-boundaries-docs/docs/api/>`__
-  `Update data in the API <https://opennorth.github.io/represent-boundaries-docs/docs/manage/>`__
-  `Read the API
   reference <https://opennorth.github.io/represent-boundaries-docs/docs/reference/>`__

Testing
-------

::

    createdb represent_boundaries_test
    psql represent_boundaries_test -c 'CREATE EXTENSION postgis;'
    env DJANGO_SETTINGS_MODULE=settings django-admin migrate --noinput
    python runtests.py

Acknowledgements
----------------

Represent Boundaries is based on the Chicago Tribune's
`django-boundaryservice <https://github.com/newsapps/django-boundaryservice>`__.

Released under the MIT license

.. |PyPI version| image:: https://badge.fury.io/py/represent-boundaries.svg
   :target: https://badge.fury.io/py/represent-boundaries
.. |Build Status| image:: https://github.com/opennorth/represent-boundaries/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/opennorth/represent-boundaries/actions/workflows/ci.yml
.. |Coverage Status| image:: https://coveralls.io/repos/opennorth/represent-boundaries/badge.png?branch=master
   :target: https://coveralls.io/r/opennorth/represent-boundaries

Represent Boundaries
====================

|PyPI version| |Build Status| |Dependency Status| |Coverage Status|

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

Represent Boundaries is one of many `Poplus
Components <http://poplus.org/components/>`__: independent pieces of
software developed to solve a range of common problems encountered when
building civic and democratic websites. `Check out the other
components. <http://poplus.org/components/current/>`__

Documentation
-------------

-  `Installation <http://represent.poplus.org/docs/install/>`__
-  `Add data to the API <http://represent.poplus.org/docs/import/>`__
-  `Use the API <http://represent.poplus.org/docs/api/>`__
-  `Update data in the API <http://represent.poplus.org/docs/manage/>`__
-  `Read the API
   reference <http://represent.poplus.org/docs/reference/>`__

Testing
-------

::

    createdb travis_ci_test
    psql travis_ci_test -c 'CREATE EXTENSION postgis;'
    django-admin.py migrate --settings settings --noinput
    python runtests.py

Acknowledgements
----------------

Represent Boundaries is based on the Chicago Tribune's
`django-boundaryservice <https://github.com/newsapps/django-boundaryservice>`__.

Released under the MIT license

.. |PyPI version| image:: https://badge.fury.io/py/represent-boundaries.svg
   :target: https://badge.fury.io/py/represent-boundaries
.. |Build Status| image:: https://secure.travis-ci.org/opennorth/represent-boundaries.png
   :target: https://travis-ci.org/opennorth/represent-boundaries
.. |Dependency Status| image:: https://gemnasium.com/opennorth/represent-boundaries.png
   :target: https://gemnasium.com/opennorth/represent-boundaries
.. |Coverage Status| image:: https://coveralls.io/repos/opennorth/represent-boundaries/badge.png?branch=master
   :target: https://coveralls.io/r/opennorth/represent-boundaries

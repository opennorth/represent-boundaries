# Represent Boundaries

Represent Boundaries is a web API to geographic areas, like electoral districts. It allows you to easily find the areas that cover your users' locations to display location-based information, like profiles of electoral candidates.

It's a Django app that's easy to integrate into an existing project or to deploy on its own. It uses a simple file format to control how data is loaded into the API, and it provides a command-line tool to easily manage data.

Notable uses include:

* [Represent](http://represent.opennorth.ca) helps people find the elected officials and electoral districts for any Canadian address or postal code, at any level of government.
* [OpenStates.org](http://openstates.org/find_your_legislator/) allows anyone to discover more about lawmaking in their state and uses Represent Boundaries to help them find their state legislators.
* [GovTrack.us](https://www.govtrack.us/congress/members) helps track the activities of the United States Congress and uses Represent Boundaries to help people find their members of Congress.
* [ANCFinder.org](http://ancfinder.org/) helps Washington, DC residents discover and participate in their Advisory Neighborhood Commissions.

Public instances include:

* [represent.opennorth.ca](http://represent.opennorth.ca) for Canada: [source code](https://github.com/opennorth/represent-canada) and [data files](https://github.com/opennorth/represent-canada-data)
* [gis.govtrack.us](http://gis.govtrack.us/map/demo/cd-2012/) for the US: [source code](https://github.com/JoshData/boundaries_us)

Represent Boundaries is one of many [Poplus Components](http://poplus.org/components/): independent pieces of software developed to solve a range of common problems encountered when building civic and democratic websites. [Check out the other components.](http://poplus.org/components/current/)

## Documentation

* [Installation](http://represent.poplus.org/docs/install/)
* [Add data to the API](http://represent.poplus.org/docs/import/)
* [Use the API](http://represent.poplus.org/docs/api/)
* [Update data in the API](http://represent.poplus.org/docs/manage/)
* [Read the API reference](http://represent.poplus.org/docs/reference/)

## Acknowledgements

Represent Boundaries is based on the Chicago Tribune's [django-boundaryservice](http://github.com/newsapps/django-boundaryservice).

## Bugs? Questions?

This project's main repository is on GitHub: [http://github.com/opennorth/represent-boundaries](http://github.com/opennorth/represent-boundaries), where your contributions, forks, bug reports, feature requests, and feedback are greatly welcomed.

Released under the MIT license

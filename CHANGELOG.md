# Changelog

## 0.10.1 (2024-06-26)

* Make boundary set slug editable.

## 0.10.0 (2024-06-26)

* Replace n-dashes and m-dashes in boundary set slugs with hyphens.
* Add support for Django 3.2 and 4.2.
* Drop support for Python <= 3.7.

## 0.9.4 (2019-01-09)

* Add support for Django 2.1.

## 0.9.3 (2018-08-04)

* `analyzeshapefiles` outputs boundary sets in alphabetical order by name/slug.

## 0.9.2 (2018-03-25)

* Support shapefiles with date field values.
* Add support for Django 2.0.
* Drop support for Django <= 1.10.

## 0.9.1 (2017-02-23)

* Fix packaging (was omitting data files during install).

## 0.9.0 (2017-02-23)

* Use Django 1.9's `JSONField` to migrate to PostgreSQL 9.4's `jsonb` datatype.
* Drop support for Django <= 1.8.
* Drop support for PostgreSQL <= 9.3.

## 0.8.1 (2017-02-23)

* Add `analyzeshapefiles` command to report the number of features to be loaded, along with names and identifiers.
* Fix `compute_intersections` for Django 1.10.
* Fix packaging for recent Django.
* Remove South migrations.

## 0.8.0 (2017-02-13)

* Add support for Django 1.9 and 1.10.
* Drop support for Django <= 1.7 and Python 2.6 and 3.3.

## 0.7.5 (2016-02-25)

* Allow `$` and `.` in JSONP callback. The callback validation can be [further improved](http://tav.espians.com/sanitising-jsonp-callback-identifiers-for-security.html).

## 0.7.4 (2015-10-05)

* Add `boundaries.migrations` to package.

## 0.7.3 (2015-10-05)

* Fix `SourceFileLoader` being unavailable prior to Python 3.3.

## 0.7.2 (2015-10-05)

* Drop support for undocumented `metadata` key in definition files.

## 0.7.1 (2015-09-25)

* Add `start_date` and `end_date` to boundaries. [#31](https://github.com/opennorth/represent-boundaries/pull/31) (@mileswwatkins)
* Increase length of `external_id` to 255 characters. [#32](https://github.com/opennorth/represent-boundaries/pull/32) (@evz)
* Add `blank=True` to `JSONField` for Django 1.9. [#33](https://github.com/opennorth/represent-boundaries/pull/33) (@jamesturk)

## 0.7.0 (2015-04-24)

* Fix definition file loader to use an importer instead of `eval` [#30](https://github.com/opennorth/represent-boundaries/pull/30) (@paultag)
  * If you were using `re` or other modules imported by `boundaries/__init__.py` in your definition files without importing them in your definition files, you must now import them in your definition files.

## 0.6.5 (2015-01-30)

* Relax `jsonfield` version requirements.
* Fix assignment of default `srs` in `Feature` class, which was breaking Heroku static assets.

## 0.6.4 (2015-01-06)

* Fix regression in slugless definition files.

## 0.6.3 (2014-12-29)

* Eliminate Django 1.7 deprecation warning.

## 0.6.2 (2014-11-29)

* Set default value on `jsonfield` fields.

## 0.6.1 (2014-11-29)

* Use `jsonfield` instead of `django-jsonfield`.

## 0.6.0 (2014-10-19)

* Support shapefiles with binary field names.
* Recurse directories and ZIP files in `loadshapefiles`.
* `loadshapefiles` will not create a boundary set if no shapefiles are found.

Identified quirks:

* If a shapefile has `_cleaned_` in its name, it will not be loaded, unless created by Represent Boundaries.

## 0.5.1 (2014-09-12)

* Fix regression with `loadshapefiles` skip logic.

## 0.5.0 (2014-08-28)

* Remove the `--database` (`-u`) option from the `loadshapefiles` management command, which would only specify the database in which to find the `spatial_ref_sys` table.
* Make non-integer `offset` error message consistent with non-integer `limit` error message.
* `format=wkt` and `format=kml` no longer error in Django 1.7.
* I18n support.
* Add tests.

Identified quirks:

* The `shape`, `simple_shape` and `centroid` endpoints ignore the `pretty` parameter.

## 0.4.0 (2014-08-01)

* Add `start_date` and `end_date` to boundary sets. [#21](https://github.com/opennorth/represent-boundaries/pull/21) (@jamesturk)
* Remove API throttle, as this is the responsibility of a proxy. [#22](https://github.com/opennorth/represent-boundaries/pull/22) (@jamesturk)

## 0.3.2 (2014-07-01)

* Add templates and static files to package.

## 0.3.1 (2014-07-01)

* Python 3 compatibility: Fix writing ZIP file contents.

## 0.3 (2014-06-27)

* Django 1.7 compatibility.
* If the `contains` parameter is an invalid latitude and longitude pair, return the invalid pair in the error message.

## 0.2 (2014-03-26)

* Python 3 compatibility. [#14](https://github.com/opennorth/represent-boundaries/pull/14) (@jamesturk)
* Fix various small bugs and encoding issues and add help text.
* API
  * Add CORS support.
  * New API throttle.
  * If a request is made with invalid filters, return a 400 error instead of a 500 error.
  * JSON
    * Add `extent` to the detail of boundary sets.
    * Add `external_id` to the list of boundaries.
    * Add `extent`, `centroid` and `extra` to the detail of boundaries.
* Loading shapefiles
  * Calculate the geographic extent of boundary sets and boundaries.
  * Re-load a boundary set if the `last_updated` field in its definition is more recent than in the database, without having to set the `--reload` switch.
  * If two boundaries have the same slug, and the `--merge` option is set to `union` or `combine`, union their geometries or combine their geometries into a MultiPolygon.
  * Follow symbolic links when walking the shapefiles directory tree.
  * If `DEBUG = True`, prompt the user about the risk of high memory consumption. [#15](https://github.com/opennorth/represent-boundaries/pull/15) (@jamesturk)
  * Log an error if a shapefile contains no layers.
  * Add an example definition file.
  * Definition files
    * New `name` field so that a boundary set's slug and name can differ.
    * New `is_valid_func` field so that features can be excluded when loading a shapefile.
    * New `extra` field to add free-form metadata.
  * ZIP files
    * If the `--clean` switch is set, convert 3D features to 2D when loading shapefiles from ZIP files.
    * Clean up temporary files created by uncompressing ZIP files.
    * Support ZIP files containing directories.
* Management commands
  * Add a `compute_intersections` management command to report overlapping boundaries from a pair of boundary sets.
  * Remove the `startshapedefinitions` management command.

## 0.1 (2013-09-14)

This first release is a [significant refactoring](https://github.com/opennorth/represent-boundaries/commit/db2cdaa381ecde423dd68962d79811925092d4da) of [django-boundaryservice](https://github.com/newsapps/django-boundaryservice) from [this commit](https://github.com/newsapps/django-boundaryservice/commit/67e79d47d49eab444681309328dbe6554b953d69). Minor changes may not be logged.

* Don't `SELECT` geometries when retrieving boundary sets from the database.
* Fix various small bugs and encoding issues and improve error messages.
* API
  * Use plural endpoints `boundary-sets` and `boundaries` instead of `boundary-set` and `boundary`.
  * Move boundary detail endpoint from `boundaries/<boundary-slug>/` to `boundaries/<boundary-set-slug>/<boundary-slug>/`.
  * Remove some fields from list endpoints, remove geospatial fields from detail endpoints, and add geospatial endpoints.
  * Add a `touches` boundary filter.
  * Change the semantics of the `intersects` boundary filter from "intersects" to "covers or overlaps".
  * If the parameter `format=apibrowser` is present, display a HTML version of the JSON response.
  * Support `format=kml` and `format=wkt`.
  * JSON
    * Rename `name` to `name_plural`, `singular` to `name_singular`, and `boundaries` to `boundaries_url` on boundary sets.
    * Move `boundaries_url` under `related` on boundary sets.
    * Change `boundaries_url` from a list of boundary detail URLs to a boundary list URL.
    * Add `licence_url` to the detail of boundary sets.
    * Remove `slug`, `resource_uri`, `count` and `metadata_fields` from the detail of boundary sets.
    * Rename `kind` to `boundary_set_name` and `set` to `boundary_set_url` on boundaries.
    * Move `boundary_set_url` under `related` on boundaries.
    * Add `shape_url`, `simple_shape_url`, `centroid_url` and `boundaries_url` under `related` to the detail of boundaries.
    * Remove `slug`, `resource_uri` and `centroid` from the detail of boundaries.
* Loading shapefiles
  * Allow multiple `definition.py` files anywhere in the shapefiles directory tree, instead of a single `definitions.py` file.
  * Use EPSG:4326 (WGS 84, Google Maps) instead of EPSG:4269 (NAD 83, US Census) by default.
  * Add a `--reload` switch to re-load shapefiles that have already been loaded.
  * Remove the `--clear` switch.
  * Make the simplification tolerance configurable.
  * Definition files
    * Rename `ider` to `id_func`, `namer` to `name_func`, and `href` to `source_url`.
    * New `slug_func` to set a custom slug.
    * New `licence_url` field to link to a data license.
    * If `singular`, `id_func` or `slug_func` are not set, use sensible defaults.

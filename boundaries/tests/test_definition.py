from datetime import date

from django.test import TestCase

from boundaries.models import Definition

if not hasattr(TestCase, 'assertCountEqual'):  # Python < 3.2
    TestCase.assertCountEqual = TestCase.assertItemsEqual


class DefinitionTestCase(TestCase):
    maxDiff = None

    def test_str(self):
        definition = Definition({
            'name': 'Test',
            'name_func': lambda feature: '',
        })

        self.assertEqual(str(definition), 'Test')

    def test_defaults(self):
        definition = Definition({
            'name': '',
            'name_func': lambda feature: 'Test',
        })

        self.assertCountEqual(definition.dictionary.keys(), [
            'name',
            'name_func',
            'encoding',
            'domain',
            'authority',
            'source_url',
            'licence_url',
            'start_date',
            'end_date',
            'notes',
            'extra',
            'id_func',
            'slug_func',
            'is_valid_func',
            'label_point_func',
        ])

        self.assertEqual(definition['name'], '')
        self.assertEqual(definition['name_func']({}), 'Test')
        self.assertEqual(definition['encoding'], 'ascii')
        self.assertEqual(definition['domain'], '')
        self.assertEqual(definition['authority'], '')
        self.assertEqual(definition['source_url'], '')
        self.assertEqual(definition['licence_url'], '')
        self.assertEqual(definition['start_date'], None)
        self.assertEqual(definition['end_date'], None)
        self.assertEqual(definition['notes'], '')
        self.assertEqual(definition['extra'], {})
        self.assertEqual(definition['id_func']({}), '')
        self.assertEqual(definition['slug_func']({}), 'Test')
        self.assertEqual(definition['is_valid_func']({}), True)
        self.assertEqual(definition['label_point_func']({}), None)

    def test_overrides(self):
        definition = Definition({
            'name': 'Federal',
            'name_func': lambda feature: 'Name',
            'encoding': 'iso-8859-1',
            'domain': 'Canada',
            'authority': 'Her Majesty the Queen in Right of Canada',
            'source_url': 'http://data.gc.ca/data/en/dataset/48f10fb9-78a2-43a9-92ab-354c28d30674',
            'licence_url': 'http://data.gc.ca/eng/open-government-licence-canada',
            'start_date': date(2000, 1, 1),
            'end_date': date(2010, 1, 1),
            'notes': 'Notes',
            'extra': {'id': 'ocd-division/country:ca'},
            'id_func': lambda feature: 'ID',
            'slug_func': lambda feature: 'Slug',
            'is_valid_func': lambda feature: False,
            'label_point_func': lambda feature: '',
        })

        self.assertCountEqual(definition.dictionary.keys(), [
            'name',
            'name_func',
            'encoding',
            'domain',
            'authority',
            'source_url',
            'licence_url',
            'start_date',
            'end_date',
            'notes',
            'extra',
            'id_func',
            'slug_func',
            'is_valid_func',
            'label_point_func',
        ])

        self.assertEqual(definition['name'], 'Federal')
        self.assertEqual(definition['name_func']({}), 'Name')
        self.assertEqual(definition['encoding'], 'iso-8859-1')
        self.assertEqual(definition['domain'], 'Canada')
        self.assertEqual(definition['authority'], 'Her Majesty the Queen in Right of Canada')
        self.assertEqual(definition['source_url'], 'http://data.gc.ca/data/en/dataset/48f10fb9-78a2-43a9-92ab-354c28d30674')
        self.assertEqual(definition['licence_url'], 'http://data.gc.ca/eng/open-government-licence-canada')
        self.assertEqual(definition['start_date'], date(2000, 1, 1))
        self.assertEqual(definition['end_date'], date(2010, 1, 1))
        self.assertEqual(definition['notes'], 'Notes')
        self.assertEqual(definition['extra'], {'id': 'ocd-division/country:ca'})
        self.assertEqual(definition['id_func']({}), 'ID')
        self.assertEqual(definition['slug_func']({}), 'Slug')
        self.assertEqual(definition['is_valid_func']({}), False)
        self.assertEqual(definition['label_point_func']({}), '')

    def test_singular_default(self):
        definition = Definition({
            'name': 'Districts',
            'name_func': lambda feature: None,
        })
        self.assertEqual(definition['singular'], 'District')

    def test_singular_override(self):
        definition = Definition({
            'name': 'Districts',
            'name_func': lambda feature: None,
            'singular': 'Singular',
        })
        self.assertEqual(definition['singular'], 'Singular')

    def test_extra_default(self):
        definition = Definition({
            'name': '',
            'name_func': lambda feature: None,
            'extra': {'id': 'ocd-division/country:ca'},
        })
        self.assertEqual(definition['extra'], {'id': 'ocd-division/country:ca'})

    def test_get(self):
        definition = Definition({
            'name': '',
            'name_func': lambda feature: None,
        })
        self.assertEqual(definition.get('name'), '')
        self.assertEqual(definition.get('nonexistent', 'default'), 'default')

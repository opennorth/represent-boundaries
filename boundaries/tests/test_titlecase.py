from django.test import TestCase

from boundaries.titlecase import titlecase


class TitlecaseTestCase(TestCase):
    def test_uc_initials(self):
        self.assertEqual(titlecase('X.Y.Z. INC.'), 'X.Y.Z. Inc.')

    def test_apos_second(self):
        self.assertEqual(titlecase("duck à l'orange"), "Duck à L'Orange")

    def test_inline_period(self):
        self.assertEqual(titlecase('example.com'), 'example.com')

    def test_small_words(self):
        self.assertEqual(titlecase('FOR WHOM THE BELL TOLLS'), 'For Whom the Bell Tolls')

    def test_mac_mc(self):
        self.assertEqual(titlecase('MACDONALD'), 'MacDonald')

    def test_slash(self):
        self.assertEqual(titlecase('foo/bar/baz'), 'Foo/Bar/Baz')

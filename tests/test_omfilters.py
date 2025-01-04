from .omfilters import *
from datetime import datetime
import unittest

class Test_omfilters(unittest.TestCase):

    def test_remove_aspas(self):
        self.assertEqual(remove_aspas('"<teste>"'), '<teste>')

    def test_formata_int(self):
        self.assertEqual(formata_int(2.0), 2)

    def test_none_to_blank(self):
        self.assertEqual('-', none_to_blank(None))

    def test_formata_br_date(self):
        date_format = '%Y-%m-%d'
        date_obj = datetime.strptime('1997-03-15', date_format)
        self.assertEqual(formata_br_date(date_obj), '15/03/1997')

unittest.main()
#!/usr/bin/env python
from __future__ import division

__author__ = "Jai Ram Rideout"
__copyright__ = "Copyright 2012, The QIIME project"
__credits__ = ["Jai Ram Rideout"]
__license__ = "GPL"
__version__ = "1.5.0-dev"
__maintainer__ = "Jai Ram Rideout"
__email__ = "jai.rideout@gmail.com"
__status__ = "Development"

"""Test suite for the remote.py module."""

from cogent.util.unit_test import TestCase, main
from qiime.remote import (_get_cleaned_headers,
                          _extract_spreadsheet_key_from_url,
                          load_google_spreadsheet_mapping_file,
                          RemoteMappingFileConnectionError,
                          RemoteMappingFileError)

class RemoteTests(TestCase):
    """Tests for the remote.py module."""

    def setUp(self):
        """Define some sample data that will be used by the tests."""
        self.url1 = url1
        self.url2 = url2
        self.url3 = url3
        self.spreadsheet_key = '0AnzomiBiZW0ddDVrdENlNG5lTWpBTm5kNjRGbjVpQmc'
        self.worksheet_name = 'Fasting_Map'
        self.exp_mapping_lines = exp_mapping_lines

    def test_load_google_spreadsheet_mapping_file(self):
        """Test correctly retrieves a remote mapping file."""
        # If we have an active Internet connection, try the test. If not, at
        # least make sure an appropriate error is thrown.
        try:
            obs = load_google_spreadsheet_mapping_file(self.spreadsheet_key,
                                                       worksheet_name=None)
        except RemoteMappingFileConnectionError:
            pass
        else:
            self.assertEqual(obs, self.exp_mapping_lines)

    def test_get_cleaned_headers(self):
        """Test correctly converts headers to Google's representation."""
        # Some duplicates.
        exp = ['foo', 'foo_1', 'foo_2', 'foo_3', 'fooo', 'foo_4', 'foo_5']
        obs = _get_cleaned_headers(
                ['foo', 'Foo', 'FOO', 'F_oO', 'F:Oo_o', '#Foo', 'f O O#'])
        self.assertEqual(obs, exp)

        # All unique.
        exp = ['foo', 'bar']
        obs = _get_cleaned_headers(['Fo#o', 'bar'])
        self.assertEqual(obs, exp)

    def test_extract_spreadsheet_key_from_url(self):
        """Test correctly extracts a key from a URL."""
        # Pass various URLs with different key/value combos.
        obs = _extract_spreadsheet_key_from_url(self.url1)
        self.assertEqual(obs, self.spreadsheet_key)

        obs = _extract_spreadsheet_key_from_url(self.url2)
        self.assertEqual(obs, self.spreadsheet_key)

        obs = _extract_spreadsheet_key_from_url(self.url3)
        self.assertEqual(obs, self.spreadsheet_key)

        # Pass a key directly.
        obs = _extract_spreadsheet_key_from_url(self.spreadsheet_key)
        self.assertEqual(obs, self.spreadsheet_key)

        # Pass 'key=<key>'.
        obs = _extract_spreadsheet_key_from_url('key=' + self.spreadsheet_key)
        self.assertEqual(obs, self.spreadsheet_key)


url1 = 'https://docs.google.com/spreadsheet/ccc?key=0AnzomiBiZW0ddDVrdENlNG5lTWpBTm5kNjRGbjVpQmc#gid=1'

url2 = 'https://docs.google.com/spreadsheet/pub?key=0AnzomiBiZW0ddDVrdENlNG5lTWpBTm5kNjRGbjVpQmc&output=html'

url3 = 'https://docs.google.com/spreadsheet/pub?key=0AnzomiBiZW0ddDVrdENlNG5lTWpBTm5kNjRGbjVpQmc&output=html#gid=1'

exp_mapping_lines = """#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tTreatment\tDOB\tDescription
#Example mapping file for the QIIME analysis package.  These 9 samples are from a study of the effects of exercise and diet on mouse cardiac physiology (Crawford, et al, PNAS, 2009).
PC.354\tAGCACGAGCCTA\tYATGCTGCCTCCCGTAGGAGT\tControl\t20061218\tControl_mouse_I.D._354
PC.355\tAACTCGTCGATG\tYATGCTGCCTCCCGTAGGAGT\tControl\t20061218\tControl_mouse_I.D._355
PC.356\tACAGACCACTCA\tYATGCTGCCTCCCGTAGGAGT\tControl\t20061126\tControl_mouse_I.D._356
PC.481\tACCAGCGACTAG\tYATGCTGCCTCCCGTAGGAGT\tControl\t20070314\tControl_mouse_I.D._481
PC.593\tAGCAGCACTTGT\tYATGCTGCCTCCCGTAGGAGT\tControl\t20071210\tControl_mouse_I.D._593
PC.607\tAACTGTGCGTAC\tYATGCTGCCTCCCGTAGGAGT\tFast\t20071112\tFasting_mouse_I.D._607
PC.634\tACAGAGTCGGCT\tYATGCTGCCTCCCGTAGGAGT\tFast\t20080116\tFasting_mouse_I.D._634
PC.635\tACCGCAGAGTCA\tYATGCTGCCTCCCGTAGGAGT\tFast\t20080116\tFasting_mouse_I.D._635
PC.636\tACGGTGAGTGTC\tYATGCTGCCTCCCGTAGGAGT\tFast\t20080116\tFasting_mouse_I.D._636
"""


if __name__ == "__main__":
    main()

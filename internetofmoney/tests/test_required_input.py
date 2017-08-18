import unittest

from internetofmoney.RequiredField import RequiredField
from internetofmoney.RequiredInput import RequiredInput


class TestRequiredInput(unittest.TestCase):
    """
    This class contains tests that test the required input mechanism.
    """

    def setUp(self):
        self.req_fields = [RequiredField('a'), RequiredField('b')]

    def test_get_field_name_index(self):
        """
        Test whether the right index of a field name is returned
        """
        req_input = RequiredInput('abc', self.req_fields)
        self.assertEqual(req_input.get_index_of_field_name('a'), 0)
        self.assertEqual(req_input.get_index_of_field_name('b'), 1)
        self.assertEqual(req_input.get_index_of_field_name('c'), -1)

    def test_is_last_name(self):
        """
        Test the last field name check in a required input object
        """
        req_input = RequiredInput('abc', self.req_fields)
        self.assertFalse(req_input.is_last_name('a'))
        self.assertTrue(req_input.is_last_name('b'))

    def test_to_dictionary(self):
        """
        Test the to_dictionary method of a required input object
        """
        req_input = RequiredInput('abc', self.req_fields, error_text='error')
        self.assertIsInstance(req_input.to_dictionary(), dict)

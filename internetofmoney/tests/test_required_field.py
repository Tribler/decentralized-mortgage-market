import unittest

from internetofmoney.RequiredField import RequiredField


class TestRequiredField(unittest.TestCase):
    """
    This class contains tests that test the required field object.
    """

    def test_to_dictionary(self):
        """
        Test the to_dictionary method of a required field object
        """
        req_field = RequiredField('abc', text='def', placeholder='ghi')
        self.assertDictEqual(req_field.to_dictionary(),
                             {'name': 'abc', 'placeholder': 'ghi', 'text': 'def', 'type': 'text'})

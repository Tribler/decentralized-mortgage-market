from internetofmoney.tests.test_base import BaseTestCase
from internetofmoney.utils.iban import IBANUtil


class TestIbanUtil(BaseTestCase):
    """
    This class contains tests for the iban utilities
    """

    def test_bank_id_from_iban(self):
        """
        Test whether the right bank ID from an IBAN account is returned
        """
        self.assertEqual(IBANUtil.get_bank_id("NL90ABCD1324"), 'ABCD')

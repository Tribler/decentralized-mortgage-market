import os

from internetofmoney.tests.test_base import BaseTestCase
from internetofmoney.utils.permid import generate_keypair, save_keypair, read_keypair


class TestPermid(BaseTestCase):
    """
    This class contains tests for the permid utility
    """

    def test_generate_key(self):
        """
        Test generating a key
        """
        self.assertTrue(generate_keypair())

    def test_save_read_key(self):
        """
        Test reading/saving a keypair
        """
        keypair = generate_keypair()
        pair_path = os.path.join(self.temp_dir, 'ec.pem')
        save_keypair(keypair, pair_path)
        self.assertTrue(os.path.exists(pair_path))
        readed_pair = read_keypair(pair_path)
        self.assertTrue(readed_pair)

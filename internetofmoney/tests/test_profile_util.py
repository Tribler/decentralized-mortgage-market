from internetofmoney.tests.test_base import BaseTestCase
from internetofmoney.utils.profile import ProfileUtil


class TestProfileUtils(BaseTestCase):
    """
    This class contains tests for the profile utilities
    """

    def test_generate_profile_id(self):
        """
        Test generation of a profile id
        """
        rand_id = ProfileUtil.generate_profile_id()
        self.assertEqual(len(rand_id), 36)
        self.assertEqual(len(rand_id.split("-")), 5)

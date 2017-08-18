from dispersy.util import blocking_call_on_reactor_thread
from internetofmoney.database import InternetOfMoneyDB
from internetofmoney.tests.util.twisted_thread import reactor

from internetofmoney.managers.BaseManager import BaseManager
from internetofmoney.tests.test_base import BaseTestCase
from internetofmoney.tests.util.twisted_thread import deferred

from twisted.internet.defer import succeed


class TestBaseManager(BaseTestCase):
    """
    This class contains tests for the base manager
    """

    @blocking_call_on_reactor_thread
    def setUp(self):
        super(TestBaseManager, self).setUp()
        database = InternetOfMoneyDB(self.temp_dir)
        self.base_manager = BaseManager(database, cache_dir=self.temp_dir)
        self.base_manager.persistent_storage_filename = lambda: 'test'

    def test_load_save_storage(self):
        """
        Test loading and saving storage
        """
        self.base_manager.persistent_storage['test'] = 123
        self.base_manager.save_storage()
        self.base_manager.load_storage()
        self.assertEqual(self.base_manager.persistent_storage['test'], 123)

    @deferred(timeout=10)
    def test_monitor_transactions(self):
        """
        Test monitoring transactions of a base manager
        """
        self.base_manager.get_transactions = lambda: succeed([{'description': '1234'}])
        return self.base_manager.monitor_transactions('1234')

    def test_unimplemented_methods(self):
        """
        Test unimplemented methods of a base manager
        """
        self.assertRaises(NotImplementedError, self.base_manager.registered_account)
        self.assertRaises(NotImplementedError, self.base_manager.is_logged_in)
        self.assertRaises(NotImplementedError, self.base_manager.register)
        self.assertRaises(NotImplementedError, self.base_manager.login)
        self.assertRaises(NotImplementedError, self.base_manager.get_balance)
        self.assertRaises(NotImplementedError, self.base_manager.get_transactions)
        self.assertRaises(NotImplementedError, self.base_manager.get_bank_name)
        self.assertRaises(NotImplementedError, self.base_manager.get_bank_id)
        self.assertRaises(NotImplementedError, self.base_manager.perform_payment, None, None, None)

    @deferred(timeout=20)
    def test_perform_request(self):
        """
        Test the perform_request method in a manager
        """
        def on_response(response):
            self.assertTrue(response)

        return self.base_manager.perform_request('http://example.com', headers={"a": "b"}).addCallback(on_response)

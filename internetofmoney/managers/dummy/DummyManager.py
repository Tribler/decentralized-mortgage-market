from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.task import deferLater

from internetofmoney.RequiredField import RequiredField
from internetofmoney.RequiredInput import RequiredInput
from internetofmoney.managers.BaseManager import BaseManager


class DummyManager(BaseManager):

    def __init__(self, database, cache_dir='cache'):
        super(DummyManager, self).__init__(database, cache_dir)

        self.registered = True
        self.logged_in = False
        self.balance = 750
        self.transactions = []

    def persistent_storage_filename(self):
        return '%s.json' % self.get_bank_id()

    def registered_account(self):
        return self.registered

    def is_logged_in(self):
        return self.logged_in

    @staticmethod
    def get_payment_info_fields():
        """
        Return the fields required for making a payment in a Dummy manager.
        """
        amount_field = RequiredField('amount', 'text', 'Please enter the amount of money to transfer')
        destination_field = RequiredField('destination_account', 'text', 'Please enter the destination dummy IBAN')
        description_field = RequiredField('description', 'text', 'Please an optional payment description')
        return [amount_field, destination_field, description_field]

    def register(self):
        self.database.log_event('info', 'Starting registration sequence for %s' % self.get_bank_name())

        def on_register_done():
            self.registered = True
            return self.login()  # Immediately login

        return deferLater(reactor, 2, on_register_done)

    def login(self):
        self.database.log_event('info', 'Starting login sequence for %s' % self.get_bank_name())

        def on_login_done():
            self.logged_in = True

        return deferLater(reactor, 1, on_login_done)

    def get_balance(self):
        self.database.log_event('info', 'Fetching balance for %s, account %s' %
                                (self.get_bank_name(), self.get_address()))
        return succeed({"available": self.balance, "pending": 0.0, "currency": "EUR"})

    def make_payment(self):
        """
        Initiate a new payment by asking the user for payment details.
        """
        required_input = RequiredInput('dummy_payment_info', DummyManager.get_payment_info_fields())
        return self.input_handler(required_input).addCallback(self.on_entered_payment_details)

    def on_entered_payment_details(self, input):
        return self.perform_payment(float(input['amount']), input['destination_account'], input['description'])

    def perform_payment(self, amount, destination_account, description):
        self.database.log_event('info', 'Starting %s payment with amount %f to %s (description: %s)' %
                                (self.get_bank_name(), amount, destination_account, description))
        self.database.add_transaction('a' * 20, self.get_address(), destination_account, amount, description)
        self.transactions.append({"amount": amount})
        return succeed('a' * 20)

    def get_transactions(self):
        self.database.log_event('info', 'Fetching %s transactions of account %s' %
                                (self.get_bank_name(), self.get_address()))
        return succeed(self.transactions)

    def monitor_transactions(self, transaction_id):
        return succeed({"amount": 50})

    def get_address(self):
        raise NotImplementedError('Please implement this method')


class Dummy1Manager(DummyManager):

    def get_bank_name(self):
        return 'Dummy1'

    def get_bank_id(self):
        return 'DUMA'

    def get_address(self):
        return 'NL68DUMA0111111111'


class Dummy2Manager(DummyManager):

    def get_bank_name(self):
        return 'Dummy2'

    def get_bank_id(self):
        return 'DUMB'

    def get_address(self):
        return 'NL06DUMB0111111111'


class Dummy3Manager(DummyManager):

    def get_bank_name(self):
        return 'Dummy3'

    def get_bank_id(self):
        return 'DUMC'

    def get_address(self):
        return 'NL41DUMC0111111111'

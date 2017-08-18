import json
import os
from cookielib import LWPCookieJar

import keyring
import logging
from Crypto.Cipher import AES
from twisted.internet import reactor
from twisted.internet.defer import succeed, Deferred
from twisted.internet.task import LoopingCall
from twisted.web import http
from twisted.web.client import readBody, Agent, CookieAgent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implements

from dispersy.util import blocking_call_on_reactor_thread


class RequestError(Exception):
    def __init__(self, response=None, msg=None):
        Exception.__init__(self, msg)
        self.response = response


class POSTDataProducer(object):
    """
    This class is used for posting data by the requests made during the tests.
    """
    implements(IBodyProducer)

    def __init__(self, raw_data):
        self.body = raw_data
        self.length = len(self.body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class BaseManager(object):
    """
    This class serves as the base class for all bank-specific managers.
    """
    TX_POLL_DELAY = 5

    def __init__(self, database, cache_dir='cache'):
        # Fix the keyring
        # TODO this is unsafe but makes the tests pass
        if keyring.get_keyring().__class__.__name__ == "EncryptedKeyring":
            for new_keyring in keyring.backend.get_all_keyring():
                if new_keyring.__class__.__name__ == "PlaintextKeyring":
                    keyring.set_keyring(new_keyring)

        self.database = database
        self.input_handler = None
        self.entered_inputs = {}  # Keeps track of all entered inputs
        self.cookie_jar = LWPCookieJar()
        self.cache_dir = cache_dir
        self.persistent_storage = {}
        self._logger = logging.getLogger(self.__class__.__name__)
        self.load_storage()

    def registered_account(self):
        raise NotImplementedError('Please implement this method')

    def is_logged_in(self):
        raise NotImplementedError('Please implement this method')

    def register(self):
        raise NotImplementedError('Please implement this method')

    def login(self):
        raise NotImplementedError('Please implement this method')

    def get_balance(self):
        raise NotImplementedError('Please implement this method')

    def get_transactions(self):
        raise NotImplementedError('Please implement this method')

    def get_bank_name(self):
        raise NotImplementedError('Please implement this method')

    def get_bank_id(self):
        raise NotImplementedError('Please implement this method')

    def is_switch_capable(self):
        return True

    def monitor_transactions(self, transaction_id):
        """
        Monitor for a transaction with a specific identifier. Returns a deferred that fires when we received a
        transaction with this identifier.
        """
        self._logger.info("Will monitor for transaction with id %s", transaction_id)
        self.database.log_event('info', "Will monitor for transaction with id %s" % transaction_id)
        monitor_deferred = Deferred()

        def monitor_loop():
            def on_transactions(transactions):
                for transaction in transactions:
                    if transaction_id in transaction['description']:
                        self._logger.info("Found transaction with id %s", transaction_id)
                        self.database.log_event('info', "Found transaction with id %s" % transaction_id)
                        monitor_deferred.callback(transaction)
                        monitor_lc.stop()
                        break

            return self.get_transactions().addCallback(on_transactions)

        monitor_lc = LoopingCall(monitor_loop)
        # TODO we now poll at a fixed interval, this should use exponential backoff
        monitor_lc.start(self.TX_POLL_DELAY)

        return monitor_deferred

    def perform_payment(self, amount, destination_account, description):
        raise NotImplementedError('Please implement this method')

    def persistent_storage_filename(self):
        return 'base'

    def get_symmetric_key(self):
        return keyring.get_password('internetofmoney', 'symmetric_key')

    def set_symmetric_key(self, symmetric_key):
        keyring.set_password('internetofmoney', 'symmetric_key', symmetric_key)

    def load_storage(self):
        """
        Load the persistent storage. This storage is encrypted with a symmetric key which is stored in the keychain
        of the system. If this symmetric key is not available, it is generated.
        """
        self._logger.debug("Loading persistent storage")
        symmetric_key = self.get_symmetric_key()
        if not symmetric_key:
            symmetric_key = os.urandom(16).encode('hex')
            self.set_symmetric_key(symmetric_key)

        storage_file_path = os.path.join(self.cache_dir, self.persistent_storage_filename())
        if os.path.exists(storage_file_path):
            with open(storage_file_path, 'r') as storage_file:
                content = storage_file.read()

                # Decrypt the contents
                cipher = AES.new(symmetric_key, AES.MODE_CFB, '0' * 16)
                decrypted_content = cipher.decrypt(content)

                self.persistent_storage = json.loads(decrypted_content)

    def save_storage(self):
        self._logger.debug("Saving persistent storage")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Encrypt the dictionary
        contents = json.dumps(self.persistent_storage)
        symmetric_key = self.get_symmetric_key()
        cipher = AES.new(symmetric_key, AES.MODE_CFB, '0' * 16)
        encrypted_contents = cipher.encrypt(contents)

        storage_file_path = os.path.join(self.cache_dir, self.persistent_storage_filename())
        with open(storage_file_path, 'w') as storage_file:
            storage_file.write(encrypted_contents)

    def perform_request(self, url, request_type='GET', raw_data='', headers=None):
        if headers:
            # Convert all header fields to arrays
            for key in headers.keys():
                headers[key] = [headers[key]]

            headers = Headers(headers)

        def _on_error_response(response, response_str):
            raise RequestError(response, response_str)

        def _on_response(response):
            if response.code == http.OK or response.code == http.CREATED or response.code == http.PARTIAL_CONTENT:
                return readBody(response)
            else:
                return readBody(response).addCallback(lambda response_str: _on_error_response(response, response_str))

        self._logger.debug("Performing %s request to %s", request_type, url)
        agent = CookieAgent(Agent(reactor), self.cookie_jar)
        data_producer = None if request_type == 'GET' else POSTDataProducer(raw_data)
        deferred = agent.request(request_type, url, headers, data_producer)
        deferred.addCallback(_on_response)
        return deferred

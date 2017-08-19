import os
import sys
import signal
import random
import argparse
import logging.config

from base64 import urlsafe_b64encode

from schwifty.iban import IBAN
from twisted.python import log
from twisted.internet import reactor

from dispersy.crypto import LibNaCLSK
from dispersy.dispersy import Dispersy
from dispersy.endpoint import StandaloneEndpoint

from internetofmoney.moneycommunity.community import MoneyCommunity
from internetofmoney.database import InternetOfMoneyDB
from internetofmoney.managers.dummy.DummyManager import DummyManager
from internetofmoney.utils.iban import IBANUtil

from market.community.market.community import MarketCommunity
from market.defs import DEFAULT_REST_API_PORT, DEFAULT_DISPERSY_PORT, BASE_DIR
from market.models.user import Role


class BankManager(DummyManager):

    def __init__(self, *args, **kwargs):
        self.iban = str(IBAN.generate('NL', bank_code='ABNA',
                                      account_code=''.join([str(random.randint(0, 9)) for _ in range(10)])))
        super(BankManager, self).__init__(*args, **kwargs)
        self.balance = 10000000000

    def get_bank_name(self):
        return ''

    def get_bank_id(self):
        return IBANUtil.get_bank_id(self.iban)

    def get_address(self):
        return self.iban


class DispersyManager(object):

    def __init__(self, port, state_dir, keypair_fn):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.port = port
        self.state_dir = state_dir
        self.keypair_fn = keypair_fn or os.path.join(self.state_dir, 'market.pem')

        self.session = None
        self.dispersy = None
        self.community = None

    def start_dispersy(self):
        self.logger.info('Starting Dispersy on port %d with state dir %s', self.port, self.state_dir)
        endpoint = StandaloneEndpoint(self.port)
        self.dispersy = Dispersy(endpoint, self.state_dir)
        return self.dispersy.start(autoload_discovery=True)

    def start_market(self, *args, **kwargs):

        if os.path.exists(self.keypair_fn):
            self.logger.info('Using existing keypair')
            with open(self.keypair_fn, 'rb') as keypair_fp:
                keypair_bin = keypair_fp.read()
            keypair = LibNaCLSK(binarykey=keypair_bin)
        else:
            self.logger.info('Creating new keypair')
            keypair = LibNaCLSK()
            with open(self.keypair_fn, 'wb') as keypair_fp:
                keypair_fp.write(keypair.key.sk)
                keypair_fp.write(keypair.key.seed)

        self.logger.debug('Public key %s', urlsafe_b64encode(keypair.pub().key_to_bin()))
        member = self.dispersy.get_member(private_key=keypair.key_to_bin())

        database = InternetOfMoneyDB(self.state_dir)
        manager = BankManager(database, cache_dir=self.state_dir)

        money_community = self.dispersy.define_auto_load(MoneyCommunity, member, load=True)[0]
        money_community.bank_managers = {manager.get_bank_id(): manager}

        self.logger.info('Starting MarketCommunity')
        kwargs['money_community'] = money_community
        self.community = self.dispersy.define_auto_load(MarketCommunity, member, load=True, args=args, kargs=kwargs)[0]

    def stop_dispersy(self):
        self.logger.info('Stopping Dispersy')
        return self.dispersy.stop()


def main(argv):
    logging.config.fileConfig(os.path.join(os.path.dirname(BASE_DIR), 'logger.conf'))

    type_unicode = lambda s: unicode(s, sys.getfilesystemencoding())

    parser = argparse.ArgumentParser(add_help=False, description=('Run the MarketCommunity'))
    parser.add_argument('--dispersy', help='Dispersy port', type=int, default=DEFAULT_DISPERSY_PORT)
    parser.add_argument('--api', help='API port', type=int, default=DEFAULT_REST_API_PORT)
    parser.add_argument('--state', help='State directory', type=type_unicode, default=os.path.join(BASE_DIR, 'State'))
    parser.add_argument('--keypair', help='Keypair filename', type=type_unicode)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--bank', action='store_const', const=Role.FINANCIAL_INSTITUTION, help='Run as bank')
    group.add_argument('--investor', action='store_const', const=Role.INVESTOR, help='Run as investor')
    group.add_argument('--borrower', action='store_const', const=Role.BORROWER, help='Run as borrower')

    args = parser.parse_args(sys.argv[1:])
    manager = DispersyManager(args.dispersy, args.state, args.keypair)
    role = args.bank or args.investor or args.borrower

    def start():
        # Redirect twisted log to standard python logging
        observer = log.PythonLoggingObserver()
        observer.start()

        manager.start_dispersy()
        manager.start_market(role=role, rest_api_port=args.api, database_fn='market.db')

        signal.signal(signal.SIGINT, lambda signum, stack: stop())

    def stop():
        manager.stop_dispersy().addBoth(lambda _: reactor.stop())

    reactor.callWhenRunning(start)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv[1:])

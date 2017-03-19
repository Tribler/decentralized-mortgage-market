import os
import sys
import argparse
import signal
import logging.config

from twisted.python import log
from twisted.internet import reactor

from market.dispersy.crypto import LibNaCLSK
from market.dispersy.dispersy import Dispersy
from market.dispersy.endpoint import StandaloneEndpoint
from market.community.community import MarketCommunity
from market.defs import DEFAULT_REST_API_PORT, DEFAULT_DISPERSY_PORT, BASE_DIR
from market.models.user import Role


class DispersyManager(object):

    def __init__(self, port, state_dir):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.port = port
        self.state_dir = state_dir

        self.session = None
        self.dispersy = None
        self.community = None

    def start_dispersy(self):
        self.logger.info('Starting Dispersy on port %d with state dir %s', self.port, self.state_dir)
        endpoint = StandaloneEndpoint(self.port)
        self.dispersy = Dispersy(endpoint, self.state_dir)
        return self.dispersy.start(autoload_discovery=True)

    def start_market(self, *args, **kwargs):
        self.logger.info('Starting MarketCommunity')

        keypair_fn = os.path.join(self.dispersy.working_directory, 'market.pem')
        if os.path.exists(keypair_fn):
            self.logger.info('Using existing keypair')
            with open(keypair_fn, 'rb') as keypair_fp:
                keypair_bin = keypair_fp.read()
            keypair = LibNaCLSK(binarykey=keypair_bin)
        else:
            self.logger.info('Creating new keypair')
            keypair = LibNaCLSK()
            with open(keypair_fn, 'wb') as keypair_fp:
                keypair_fp.write(keypair.key.sk)
                keypair_fp.write(keypair.key.seed)

        member = self.dispersy.get_member(private_key=keypair.key_to_bin())
        self.community = self.dispersy.define_auto_load(MarketCommunity, member, load=True, args=args, kargs=kwargs)[0]

    def stop_dispersy(self):
        self.logger.info('Stopping Dispersy')
        return self.dispersy.stop()


def main(argv):
    logging.config.fileConfig(os.path.join(os.path.dirname(BASE_DIR), 'logger.conf'))

    type_unicode = lambda s : unicode(s, sys.getfilesystemencoding())

    parser = argparse.ArgumentParser(add_help=False, description=('Run the MarketCommunity'))
    parser.add_argument('--dispersy', help='Dispersy port', type=int, default=DEFAULT_DISPERSY_PORT)
    parser.add_argument('--api', help='API port', type=int, default=DEFAULT_REST_API_PORT)
    parser.add_argument('--state', help='State directory', type=type_unicode, default=os.path.join(BASE_DIR, 'State'))

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--bank', action='store_const', const=Role.FINANCIAL_INSTITUTION, help='Run as bank')
    group.add_argument('--investor', action='store_const', const=Role.INVESTOR, help='Run as investor')
    group.add_argument('--borrower', action='store_const', const=Role.BORROWER, help='Run as borrower')

    args = parser.parse_args(sys.argv[1:])
    manager = DispersyManager(args.dispersy, args.state)
    role = args.bank or args.investor or args.borrower

    def start():
        # Redirect twisted log to standard python logging
        observer = log.PythonLoggingObserver()
        observer.start()

        manager.start_dispersy()
        manager.start_market(role, args.api)

        signal.signal(signal.SIGINT, lambda signum, stack: stop())

    def stop():
        manager.stop_dispersy().addBoth(lambda _: reactor.stop())

    reactor.callWhenRunning(start)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv[1:])

import os
import sys
import argparse
import signal
import logging

from twisted.internet import reactor

from market.dispersy.dispersy import Dispersy
from market.dispersy.endpoint import StandaloneEndpoint
from market.community.community import MortgageCommunity, MortgageSettings
from market.community import ROLE_BANK, ROLE_BORROWER, ROLE_INVESTOR

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))


class DispersyManager(object):

    def __init__(self, port, state_dir):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.port = port
        self.state_dir = state_dir

        self.session = None
        self.dispersy = None
        self.community = None
        self.member = None

    def start_dispersy(self):
        self.logger.info('Starting Dispersy on port %d with state dir %s', self.port, self.state_dir)
        endpoint = StandaloneEndpoint(self.port)
        self.dispersy = Dispersy(endpoint, self.state_dir)
        return self.dispersy.start(autoload_discovery=True)

    def start_market(self, **kwargs):
        self.logger.info('Starting MortgageCommunity')
        # TODO: get member from file
        self.member = self.dispersy.get_new_member(u"curve25519")
        self.community = self.dispersy.define_auto_load(MortgageCommunity, self.member, load=True, kargs=kwargs)[0]

    def stop_dispersy(self):
        self.logger.info('Stopping Dispersy')
        return self.dispersy.stop()


def main(argv):
    parser = argparse.ArgumentParser(add_help=False, description=('Run the MortgageCommunity'))
    parser.add_argument('--dispersy', help='Dispersy port')
    parser.add_argument('--api', help='API port')
    parser.add_argument('--state', help='State directory')
    parser.add_argument('--bank', action='store_true', help='Run as bank')
    parser.add_argument('--investor', action='store_true', help='Run as investor')
    parser.add_argument('--borrower', action='store_true', help='Run as borrower')

    args = parser.parse_args(sys.argv[1:])

    dispersy_port = int(args.dispersy) if args.dispersy else 7759
    api_port = int(args.api) if args.api else 7760
    state_dir = unicode(args.state or os.path.join(BASE_DIR, 'State'))

    role = 0
    if args.bank:
        role |= ROLE_BANK
    if args.investor:
        role |= ROLE_INVESTOR
    if args.borrower:
        role |= ROLE_BORROWER
    settings = MortgageSettings()
    settings.role = role


    manager = DispersyManager(dispersy_port, state_dir)

    def start():
        manager.start_dispersy()
        manager.start_market(settings=settings)

        signal.signal(signal.SIGINT, lambda signum, stack: stop())

    def stop():
        manager.stop_dispersy().addBoth(lambda _: reactor.stop())

    reactor.callWhenRunning(start)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv[1:])

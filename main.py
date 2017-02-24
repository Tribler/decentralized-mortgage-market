import os
import sys
import argparse
import signal
import logging

from twisted.internet import reactor

from dispersy.dispersy import Dispersy
from dispersy.endpoint import StandaloneEndpoint
from dispersy.crypto import M2CryptoSK
from market.community.community import MortgageMarketCommunity

from market.api.api import MarketAPI
from market.database.backends import PersistentBackend, MemoryBackend
from market.database.database import MarketDatabase
        
BASE_DIR = unicode(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)))))


class DispersyManager(object):
    
    def __init__(self, port=7759, state_dir=BASE_DIR):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.port = port
        self.state_dir = state_dir
        
        self.session = None
        self.dispersy = None
        self.community = None
        self.member = None

    def start_dispersy(self):
        self.logger.info('Starting Dispersy')
        endpoint = StandaloneEndpoint(self.port)
        self.dispersy = Dispersy(endpoint, self.state_dir)
        return self.dispersy.start()

    def start_market(self):
        self.logger.info('Starting MortgageMarketCommunity')
        # TODO: get member from file
        self.member = self.dispersy.get_new_member(u"curve25519")
        self.community = self.dispersy.define_auto_load(MortgageMarketCommunity, self.member, load=True)[0]

    def stop_dispersy(self):
        self.logger.info('Stopping Dispersy')
        return self.dispersy.stop()


def main(argv):
    manager = DispersyManager()

    def start():
        manager.start_dispersy()
        manager.start_market()
        
        api = MarketAPI(MarketDatabase(MemoryBackend()))
        
        manager.community._api = api
        manager.community.user = api.login_user(manager.member.private_key.key_to_bin().encode("HEX"))
        
        signal.signal(signal.SIGINT, lambda signum, stack: stop())
        
    def stop():
        manager.stop_dispersy().addBoth(lambda _: reactor.stop())

    reactor.callWhenRunning(start)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv[1:])

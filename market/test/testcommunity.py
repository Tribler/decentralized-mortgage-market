import sys
import logging

from tempfile import mkdtemp

# This will ensure nose starts the reactor. Do not remove
from nose.twistedtools import reactor
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.python import log
from twisted.trial import unittest

from dispersy.dispersy import Dispersy
from dispersy.endpoint import StandaloneEndpoint
from dispersy.candidate import Candidate
from dispersy.util import blocking_call_on_reactor_thread

# Redirect twisted log to standard python logging
observer = log.PythonLoggingObserver()
observer.start()

class TestCommunity(unittest.TestCase):

    def setUp(self):
        # Nose prints to stderr, so we will use stdout
        self.handler = logging.StreamHandler(sys.stdout)
        for logger_name in ['MarketLogger', 'BlockchainLogger']:
            logger = logging.getLogger(logger_name)
            logger.addHandler(self.handler)
            logger.setLevel(logging.DEBUG)

        super(TestCommunity, self).setUp()
        self.communities = []
        self.message_callbacks = {}

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def tearDown(self):
        super(TestCommunity, self).tearDown()

        for community in self.communities[:]:
            yield self.destroy_community(community)

        for logger_name in ['MarketLogger', 'BlockchainLogger']:
            logging.getLogger(logger_name).removeHandler(self.handler)

    def create_community(self, cls, *args, **kwargs):
        temp_dir = unicode(mkdtemp(suffix="_dispersy_test_session"))

        dispersy = Dispersy(StandaloneEndpoint(0), temp_dir, database_filename=u':memory:')
        dispersy.start(autoload_discovery=False)

        my_member = dispersy.get_new_member(u'curve25519')

        if self.communities:
            head_community = self.communities[0]
            master_member = dispersy.get_member(mid=head_community._master_member.mid)
            community = cls.init_community(dispersy, master_member, my_member, *args, **kwargs)
            community.candidates.clear()
            community.add_discovered_candidate(Candidate(head_community.dispersy.lan_address, False))
        else:
            community = cls.create_community(dispersy, my_member, *args, **kwargs)
            community.candidates.clear()

        self.attach_hooks(community)
        self.communities.append(community)

        return community

    @inlineCallbacks
    def destroy_community(self, community):
        if community.dispersy.running:
            yield community.dispersy.stop()
        self.message_callbacks.pop(community, None)
        self.communities.remove(community)

    def attach_hooks(self, community):
        # Attach message hooks
        def hook(messages, callback):
            callback(messages)

            for message in messages:
                if message.name in self.message_callbacks.get(community, {}):
                    deferreds = self.message_callbacks[community].pop(message.name)
                    for deferred in deferreds:
                        deferred.callback(message)

        for meta_message in community.get_meta_messages():
            meta_message._handle_callback = lambda msgs, cb = meta_message.handle_callback: hook(msgs, cb)

    def get_next_message(self, community, message_name):
        def timeout(d):
            deferreds = self.message_callbacks.get(community, {}).get(message_name, [])
            if d in deferreds:
                deferreds.remove(d)
                d.errback(RuntimeError('get_next_message timeout'))

        deferred = Deferred()
        community.register_task(deferred, reactor.callLater(10, timeout, deferred))
        self.message_callbacks[community] = self.message_callbacks.get(community, {})
        self.message_callbacks[community][message_name] = self.message_callbacks.get(message_name, [])
        self.message_callbacks[community][message_name].append(deferred)
        return deferred

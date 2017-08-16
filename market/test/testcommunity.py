import sys
import logging
import unittest

from tempfile import mkdtemp

# This will ensure nose starts the reactor. Do not remove
from nose.twistedtools import reactor
from twisted.internet.defer import Deferred
from twisted.python import log

from dispersy.dispersy import Dispersy
from dispersy.endpoint import StandaloneEndpoint
from dispersy.candidate import Candidate

logging.basicConfig(stream=sys.stderr)
logging.getLogger("MarketLogger").setLevel(logging.DEBUG)

# Redirect twisted log to standard python logging
observer = log.PythonLoggingObserver()
observer.start()

class TestCommunity(unittest.TestCase):

    def setUp(self):
        super(TestCommunity, self).setUp()
        self.communities = []
        self.message_callbacks = {}

    def tearDown(self):
        super(TestCommunity, self).tearDown()

        for community in self.communities:
            community.dispersy.stop()

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
            community = cls.create_community(dispersy, my_member)
            community.candidates.clear()

        self.attach_hooks(community)
        self.communities.append(community)

        return community

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
                raise Exception('get_next_message timeout')

        deferred = Deferred()
        reactor.callLater(10, timeout, deferred)
        self.message_callbacks[community] = self.message_callbacks.get(community, {})
        self.message_callbacks[community][message_name] = self.message_callbacks.get(message_name, [])
        self.message_callbacks[community][message_name].append(deferred)
        return deferred

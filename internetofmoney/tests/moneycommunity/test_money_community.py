from tempfile import mkdtemp

from shutil import rmtree

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import deferLater

from dispersy.tests.debugcommunity.node import DebugNode
from dispersy.tests.dispersytestclass import DispersyTestFunc
from internetofmoney.database import InternetOfMoneyDB
from internetofmoney.managers.dummy.DummyManager import Dummy1Manager, Dummy2Manager
from internetofmoney.moneycommunity.community import MoneyCommunity
from dispersy.util import blocking_call_on_reactor_thread
from twisted.internet import reactor


class TestMoneyCommunity(DispersyTestFunc):

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self):
        yield DispersyTestFunc.setUp(self)

        self.temp_dir = mkdtemp(suffix="_iom_tests")

        database = InternetOfMoneyDB(self.temp_dir)

        self.dummy1_a = Dummy1Manager(database)
        self.dummy1_b = Dummy1Manager(database)
        self.dummy2_b = Dummy2Manager(database)

        self.node_a, self.node_b = yield self.create_nodes(2)
        self.node_a.community.bank_managers = {self.dummy1_a.get_bank_id(): self.dummy1_a}
        self.node_b.community.bank_managers = {self.dummy1_b.get_bank_id(): self.dummy1_b,
                                               self.dummy2_b.get_bank_id(): self.dummy2_b}

    def tearDown(self):
        DispersyTestFunc.tearDown(self)
        rmtree(unicode(self.temp_dir), ignore_errors=True)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def create_nodes(self, *args, **kwargs):
        nodes = yield super(TestMoneyCommunity, self).create_nodes(*args, community_class=MoneyCommunity,
                                                                        memory_database=False, **kwargs)
        for outer in nodes:
            for inner in nodes:
                if outer != inner:
                    outer.send_identity(inner)

        returnValue(nodes)

    def _create_node(self, dispersy, community_class, c_master_member):
        return DebugNode(self, dispersy, community_class, c_master_member, curve=u"curve25519")

    @blocking_call_on_reactor_thread
    def _create_target(self, source, destination):
        target = destination.my_candidate
        target.associate(source._dispersy.get_member(public_key=destination.my_pub_member.public_key))
        return target

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def parse_assert_packets(self, node):
        yield deferLater(reactor, 0.1, lambda: None)
        packets = node.process_packets()
        self.assertIsNotNone(packets)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_has_eligable_router(self):
        """
        Test for eligable routers in the network using two nodes
        """
        self.node_b._community.add_discovered_candidate(self.node_a.my_candidate)
        self.node_b.take_step()

        yield self.parse_assert_packets(self.node_a)  # Introduction request
        yield deferLater(reactor, 0.1, lambda: None)

        # Enough capacity
        def on_router_response(result):
            self.assertIsNotNone(result)

        deferred = self.node_a.community.has_eligable_router(
            self.dummy1_a.get_bank_id(), self.dummy2_b.get_bank_id(), 50).addCallback(on_router_response)

        yield self.parse_assert_packets(self.node_b)  # Capacity query
        yield self.parse_assert_packets(self.node_a)  # Capacity response
        yield deferred

        # Not enough capacity
        def on_router_response(result):
            self.assertIsNone(result)

        deferred = self.node_a.community.has_eligable_router(
            self.dummy1_a.get_bank_id(), self.dummy2_b.get_bank_id(), 50000).addCallback(on_router_response)

        yield self.parse_assert_packets(self.node_b)  # Capacity query
        yield self.parse_assert_packets(self.node_a)  # Capacity response
        yield deferred

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_router(self):
        """
        Test the transfer from node A (dummy 1) -> node B (switch, dummy 1/2)
        """
        @inlineCallbacks
        def on_money_sent(txid):
            self.assertIsNotNone(txid)
            transactions = yield self.dummy2_b.get_transactions()
            self.assertEqual(len(transactions), 1)

        router_candidate = self.node_b.my_candidate
        deferred = self.node_a.community.send_money_using_router(router_candidate, self.dummy1_a,
                                                                 50, 'NL68DUMA0111111111', 'NL06DUMB0111111111')\
            .addCallback(on_money_sent)

        yield self.parse_assert_packets(self.node_b)  # Payment to switch message
        yield self.parse_assert_packets(self.node_a)  # Payment from switch message
        yield deferred

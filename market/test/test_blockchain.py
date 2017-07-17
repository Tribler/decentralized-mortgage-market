import unittest
import mock

from twisted.internet.defer import inlineCallbacks, DeferredList

from market.community.market.community import BlockchainCommunity
from market.dispersy.candidate import Candidate
from market.dispersy.util import blocking_call_on_reactor_thread
from market.models import ObjectType
from market.models.contract import Contract
from market.test.testcommunity import TestCommunity


class TestBlockchainCommunity(TestCommunity):

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self):
        super(TestBlockchainCommunity, self).setUp()
        self.document = 'CONTRACT'

        # Create communities
        self.node1 = self.create_community()
        self.node2 = self.create_community()

        # Take a step (i.e., send and receive an introduction-request)
        self.node1.take_step()

        # Wait until both nodes know each other
        yield self.get_next_message(self.node1, u'dispersy-introduction-request')
        yield self.get_next_message(self.node2, u'dispersy-introduction-request')

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_contract_sign_and_store(self):
        node3 = self.create_community(verifier=False)

        self.node2.begin_contract(Candidate(node3._dispersy.lan_address, False),
                                  self.document,
                                  ObjectType.MORTGAGE,
                                  self.node2.my_member.public_key,
                                  node3.my_member.public_key,
                                  previous_hash='')

        message = yield self.get_next_message(self.node1, u'contract')

        contract = Contract.from_dict(message.payload.dictionary['contract'])
        self.assertEqual(contract.from_public_key, self.node2.my_member.public_key)
        self.assertEqual(contract.to_public_key, node3.my_member.public_key)
        self.assertEqual(contract.document, self.document)
        self.assertTrue(contract.verify())

        for community in self.communities:
            def get_next_difficulty(c, b):
                # First block should be create immediately
                return 0xffffff0000000000000000000000000000000000000000000000000000000000 if not b else 0

            community.get_next_difficulty = lambda b, c = community: get_next_difficulty(c, b)

        yield DeferredList([self.get_next_message(self.node1, u'block'),
                            self.get_next_message(self.node2, u'block')], fireOnOneCallback=True)

        first_block1 = self.node1.data_manager.get_block_indexes().first().block_id
        first_block2 = self.node2.data_manager.get_block_indexes().first().block_id

        # Check if a block is created
        self.assertTrue(first_block2)
        # Check if both bank agree on the block
        self.assertEqual(first_block2, first_block1)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_owner_request(self):
        # Create dummy contract chain. We need to create the contract twice (once for each node) or storm will complain
        node1_contract1 = self.create_contract(self.node1.my_member, self.node2.my_member)
        node1_contract2 = self.create_contract(self.node2.my_member, self.node1.my_member, node1_contract1.id)
        self.node1.data_manager.add_contract(node1_contract1)
        self.node1.data_manager.add_contract(node1_contract2)

        node2_contract1 = self.create_contract(self.node1.my_member, self.node2.my_member)
        node2_contract2 = self.create_contract(self.node2.my_member, self.node1.my_member, node2_contract1.id)
        self.node2.data_manager.add_contract(node2_contract1)
        self.node2.data_manager.add_contract(node2_contract2)

        callback = mock.Mock()
        self.node1.send_owner_request(node1_contract1.id, callback, min_responses=1)

        yield self.get_next_message(self.node2, u'owner-request')
        yield self.get_next_message(self.node1, u'owner')

        callback.assert_called_with(self.node1.my_member.public_key)

    def create_contract(self, from_member, to_member, previous_hash=''):
        contract = Contract()
        contract.from_public_key = from_member.public_key
        contract.to_public_key = to_member.public_key
        contract.document = self.document
        contract.type = ObjectType.MORTGAGE
        contract.previous_hash = previous_hash
        contract.time = 1
        contract.sign(from_member)
        contract.sign(to_member)
        return contract

    def create_community(self, *args, **kwargs):
        return super(TestBlockchainCommunity, self).create_community(BlockchainCommunity, *args, **kwargs)


if __name__ == "__main__":
    unittest.main()

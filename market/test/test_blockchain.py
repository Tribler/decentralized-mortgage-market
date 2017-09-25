import unittest

from twisted.internet.defer import inlineCallbacks

from dispersy.candidate import Candidate
from dispersy.util import blocking_call_on_reactor_thread

from market.community.market.community import BlockchainCommunity
from market.community.blockchain.community import BLOCK_GENESIS_HASH
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
        node3 = self.create_community()

        # Node2 creates a contract which node3 should sign
        self.node2.begin_contract(Candidate(node3._dispersy.lan_address, False),
                                  self.document,
                                  ObjectType.MORTGAGE,
                                  self.node2.my_member.public_key,
                                  node3.my_member.public_key,
                                  previous_hash='')

        # Wait for signature-request/response messages
        yield self.get_next_message(node3, u'signature-request')
        yield self.get_next_message(self.node2, u'signature-response')

        # Check if node1 receives the contract
        message = yield self.get_next_message(self.node1, u'contract')
        contract = Contract.from_dict(message.payload.dictionary['contract'])
        self.assertEqual(contract.from_public_key, self.node2.my_member.public_key)
        self.assertEqual(contract.to_public_key, node3.my_member.public_key)
        self.assertEqual(contract.document, self.document)
        self.assertTrue(contract.verify())

        # Let node1 store the contract in a block
        self.set_fixed_difficulty()
        self.node1.create_block()

        # Wait for the block to be receive by node2 and check the blockchains
        yield self.get_next_message(self.node2, u'block')
        node1_block1 = list(self.node1.data_manager.get_block_indexes())[-1].block_id
        node2_block1 = list(self.node2.data_manager.get_block_indexes())[-1].block_id

        # Check if a block is created
        self.assertTrue(node2_block1)
        # Check if both bank agree on the block
        self.assertEqual(node2_block1, node1_block1)

    @blocking_call_on_reactor_thread
    def test_contract_order(self):
        self.set_fixed_difficulty()

        c1 = self.create_contract(self.node1, self.node2)
        c2 = self.create_contract(self.node1, self.node2, previous_hash=c1.id)

        self.node1.incoming_contracts[c2.id] = c2
        self.node1.create_block()

        # c2 should not be on the blockchain yet, since it has c1 as dependency
        self.assertTrue(self.node1.incoming_contracts.values() == [c2])

        self.node1.incoming_contracts[c1.id] = c1
        self.node1.create_block()

        # c1 should be on the blockchain
        self.assertTrue(self.node1.incoming_contracts.values() == [c2])

        self.node1.create_block()

        # c2 should be on the blockchain
        self.assertTrue(self.node1.incoming_contracts.values() == [])

        # Check blockchain
        contract_ids = []
        for block_index in reversed(list(self.node1.data_manager.get_block_indexes())):
            if block_index.block_id != BLOCK_GENESIS_HASH:
                block = self.node1.data_manager.get_block(block_index.block_id)
                contract_ids += [c.id for c in block.contracts]
        self.assertTrue(contract_ids == [c1.id, c2.id])

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_traversal_request(self):
        self.set_fixed_difficulty()

        # Create dummy contract chain.
        c1 = self.create_contract(self.node1, self.node2)
        c2 = self.create_contract(self.node2, self.node1, previous_hash=c1.id)
        self.node1.incoming_contracts[c1.id] = c1
        self.node1.incoming_contracts[c2.id] = c2

        # The contracts should not be on the blockchain yet, so send_traversal_request should return None
        contract, confirmations = yield self.node2.send_traversal_request(c1.id)
        self.assertEqual(contract, None)
        self.assertEqual(confirmations, None)

        # Mine both blocks
        self.node1.create_block()
        self.node1.create_block()

        # Node1 should be owner
        contract, confirmations = yield self.node2.send_traversal_request(c1.id)
        self.assertEqual(contract.to_public_key, self.node1.my_member.public_key)
        self.assertEqual(confirmations, 1)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_block_request(self):
        yield self.destroy_community(self.node2)

        # Create some blocks.
        self.set_fixed_difficulty()
        blocks = [self.node1.create_block() for _ in range(2)]

        # Restart the 2nd verifier.
        self.node2 = self.create_community()
        self.node2.take_step()
        yield self.get_next_message(self.node2, u'dispersy-introduction-request')

        # Create another block. Note that node2 is now online, and it should receive the block as well.
        self.set_fixed_difficulty()
        blocks.append(self.node1.create_block())

        # Wait for the block to arrive at node2.
        yield self.get_next_message(self.node2, u'block')

        # When node2 receives the new block it should realize it doesn't yet possess the parent blocks.
        # Node2 should make block-requests.
        for _ in range(len(blocks) - 1):
            yield self.get_next_message(self.node1, u'block-request')
            yield self.get_next_message(self.node2, u'block')

        # Check if all blocks are on node2's blockchain
        for index, block in enumerate(blocks):
            db_block = self.node2.data_manager.get_block_index(block.id)
            self.assertTrue(db_block)
            self.assertEqual(index + 1, db_block.height)

    def set_fixed_difficulty(self):
        for community in self.communities:
            def get_next_difficulty(c, b):
                # Mine all blocks (almost) instantly
                return 0xffffff0000000000000000000000000000000000000000000000000000000000

            community.get_next_difficulty = lambda b, c = community: get_next_difficulty(c, b)

    def create_contract(self, from_node, to_node, previous_hash='', object_type=ObjectType.MORTGAGE):
        contract = Contract()
        contract.from_public_key = from_node.my_member.public_key
        contract.to_public_key = to_node.my_member.public_key
        contract.document = self.document
        contract.type = object_type
        contract.previous_hash = previous_hash
        contract.time = 1
        contract.sign(from_node.my_member)
        contract.sign(to_node.my_member)
        return contract

    def create_community(self, *args, **kwargs):
        # Note that we are setting verifier=False so that we can manually create blocks
        return super(TestBlockchainCommunity, self).create_community(BlockchainCommunity, *args,
                                                                     verifier=False, **kwargs)


if __name__ == "__main__":
    unittest.main()

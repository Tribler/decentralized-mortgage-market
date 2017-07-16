import os
import time
import hashlib
import logging

from base64 import b64encode
from collections import OrderedDict, defaultdict
from twisted.internet.task import LoopingCall

from market.community.blockchain.conversion import BlockchainConversion
from market.community.payload import ProtobufPayload
from market.database.datamanager import BlockchainDataManager
from market.dispersy.authentication import MemberAuthentication
from market.dispersy.candidate import Candidate
from market.dispersy.community import Community
from market.dispersy.conversion import DefaultConversion
from market.dispersy.destination import CandidateDestination
from market.dispersy.distribution import DirectDistribution
from market.dispersy.message import Message
from market.dispersy.resolution import PublicResolution
from market.dispersy.requestcache import RandomNumberCache
from market.models.block import Block
from market.models.block_index import BlockIndex
from market.models.contract import Contract
from market.util.misc import median
from market.util.uint256 import full_to_uint256, compact_to_uint256, uint256_to_compact

COMMIT_INTERVAL = 60

BLOCK_CREATION_INTERNAL = 1
BLOCK_TARGET_SPACING = 300  # 10 * 60
BLOCK_TARGET_TIMESPAN = 20 * 60  # 14 * 24 * 60 * 60
BLOCK_TARGET_BLOCKSPAN = BLOCK_TARGET_TIMESPAN / BLOCK_TARGET_SPACING
BLOCK_DIFFICULTY_INIT = 0x00ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
BLOCK_DIFFICULTY_MIN = 0x00ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
BLOCK_GENESIS_HASH = '\00' * 32

MAX_CLOCK_DRIFT = 15 * 60
MAX_PACKET_SIZE = 1500


class SignatureRequestCache(RandomNumberCache):

    def __init__(self, community):
        super(SignatureRequestCache, self).__init__(community.request_cache, u'signature-request')
        self.community = community

    def on_timeout(self):
        pass


class BlockRequestCache(RandomNumberCache):

    def __init__(self, community, block_id):
        super(BlockRequestCache, self).__init__(community.request_cache, u'block-request')
        self.community = community
        self.block_id = block_id

    def on_timeout(self):
        # Retry to download block
        self.community.send_block_request(self.block_id)


class BlockchainCommunity(Community):

    def __init__(self, dispersy, master, my_member):
        super(BlockchainCommunity, self).__init__(dispersy, master, my_member)
        self.logger = logging.getLogger('BlockchainLogger')
        self.incoming_contracts = OrderedDict()
        self.incoming_blocks = {}
        self.data_manager = None

    def initialize(self, verifier=True, **db_kwargs):
        super(BlockchainCommunity, self).initialize()

        self.initialize_database(**db_kwargs)

        if verifier:
            self.register_task('create_block', LoopingCall(self.create_block)).start(BLOCK_CREATION_INTERNAL)
        self.register_task('commit', LoopingCall(self.data_manager.commit)).start(COMMIT_INTERVAL)

        self.logger.info('Blockchain initialized')

    def initialize_database(self, database_fn=''):
        if database_fn:
            database_fn = os.path.join(self.dispersy.working_directory, database_fn)
        self.data_manager = BlockchainDataManager(database_fn)
        self.data_manager.initialize()

    @classmethod
    def get_master_members(cls, dispersy):
        # generated: Fri Feb 24 11:22:22 2017
        # curve: None
        # len: 571 bits ~ 144 bytes signature
        # pub: 170 3081a7301006072a8648ce3d020106052b81040027038192000407b
        # acf5ae4d3fe94d49a7f94b7239e9c2d878b29f0fbdb7374d5b6a09d9d6fba80d
        # 3807affd0ba45ba1ac1c278ca59bec422d8a44b5fefaabcdd62c2778414c01da
        # 4578b304b104b00eec74de98dcda803b79fd1783d76cc1bd7aab75cfd8fff982
        # 7a9647ae3c59423c2a9a984700e7cb43b881a6455574032cc11dba806dba9699
        # f54f2d30b10eed5c7c0381a0915a5
        # pub-sha1 56553661e30b342b2fc39f1a425eb612ef8b8c33
        # -----BEGIN PUBLIC KEY-----
        # MIGnMBAGByqGSM49AgEGBSuBBAAnA4GSAAQHus9a5NP+lNSaf5S3I56cLYeLKfD7
        # 23N01bagnZ1vuoDTgHr/0LpFuhrBwnjKWb7EItikS1/vqrzdYsJ3hBTAHaRXizBL
        # EEsA7sdN6Y3NqAO3n9F4PXbMG9eqt1z9j/+YJ6lkeuPFlCPCqamEcA58tDuIGmRV
        # V0AyzBHbqAbbqWmfVPLTCxDu1cfAOBoJFaU=
        # -----END PUBLIC KEY-----
        master_key = '3081a7301006072a8648ce3d020106052b81040027038192000407bacf5ae4d3fe94d49a7f94b7239e9c2d878b29' + \
                     'f0fbdb7374d5b6a09d9d6fba80d3807affd0ba45ba1ac1c278ca59bec422d8a44b5fefaabcdd62c2778414c01da4' + \
                     '578b304b104b00eec74de98dcda803b79fd1783d76cc1bd7aab75cfd8fff9827a9647ae3c59423c2a9a984700e7c' + \
                     'b43b881a6455574032cc11dba806dba9699f54f2d30b10eed5c7c0381a0915a5'
        master = dispersy.get_member(public_key=master_key.decode('hex'))
        return [master]

    def initiate_meta_messages(self):
        meta_messages = super(BlockchainCommunity, self).initiate_meta_messages()

        return meta_messages + [
            Message(self, u"signature-request",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_signature_request),
            Message(self, u"signature-response",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_signature_response),
            Message(self, u"contract",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_contract),
            Message(self, u"block-request",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_block_request),
            Message(self, u"block",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_block)
        ]

    def initiate_conversions(self):
        return [DefaultConversion(self), BlockchainConversion(self)]

    def send_message(self, msg_type, candidates, payload_dict):
        self.logger.debug('Sending %s message to %d candidate(s)', msg_type, len(candidates))
        meta = self.get_meta_message(msg_type)
        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            destination=candidates,
                            payload=(payload_dict,))
        return self.dispersy.store_update_forward([message], False, False, True)

    def multicast_message(self, msg_type, payload_dict, exclude=None):
        candidates = list(self.dispersy.dispersy_yield_verified_candidates())

        if exclude in candidates:
            candidates.remove(exclude)

        return self.send_message(msg_type, tuple(candidates), payload_dict)

    def send_signature_request(self, contract, candidate):
        cache = self.request_cache.add(SignatureRequestCache(self))
        return self.send_message(u'signature-request', (candidate,), {'identifier': cache.number,
                                                                      'contract': contract.to_dict()})

    def on_signature_request(self, messages):
        for message in messages:
            contract = Contract.from_dict(message.payload.dictionary['contract'])
            if contract is None:
                self.logger.warning('Dropping invalid signature-request from %s', message.candidate.sock_addr)
                continue
            elif not contract.verify(message.candidate.get_member()):
                self.logger.warning('Dropping signature-request with incorrect signature')
                continue

            self.logger.debug('Got signature-request from %s', message.candidate.sock_addr)

            if self.finalize_contract(contract, sign=True):
                self.send_signature_response(message.candidate, contract, message.payload.dictionary['identifier'])
                self.incoming_contracts[contract.id] = contract
                self.multicast_message(u'contract', {'contract': contract.to_dict()})

    def send_signature_response(self, candidate, contract, identifier):
        return self.send_message(u'signature-response', (candidate,), {'identifier': identifier,
                                                                       'contract': contract.to_dict()})

    def on_signature_response(self, messages):
        for message in messages:
            cache = self.request_cache.get(u'signature-request', message.payload.dictionary['identifier'])
            if not cache:
                self.logger.warning("Dropping unexpected signature-response from %s", message.candidate.sock_addr)
                continue

            contract = Contract.from_dict(message.payload.dictionary['contract'])
            if contract is None:
                self.logger.warning('Dropping invalid signature-response from %s', message.candidate.sock_addr)
                continue
            elif not contract.verify(message.candidate.get_member()):
                self.logger.warning('Dropping signature-response with incorrect signature')
                continue

            self.logger.debug('Got signature-response from %s', message.candidate.sock_addr)

            if self.finalize_contract(contract):
                self.incoming_contracts[contract.id] = contract
                self.multicast_message(u'contract', {'contract': contract.to_dict()})

    def on_contract(self, messages):
        for message in messages:
            contract = Contract.from_dict(message.payload.dictionary['contract'])
            if self.incoming_contracts.get(contract.id) or self.data_manager.get_contract(contract.id):
                self.logger.debug('Dropping contract %s (duplicate)', b64encode(contract.id))
                continue

            # Preliminary check to see if contract is allowed. A final check will be performed in check_block.
            if not self.check_contract(contract, fail_without_parent=False):
                self.logger.warning('Dropping contract %s (check failed)', b64encode(contract.id))
                continue

            self.logger.debug('Got contract %s', b64encode(contract.id))

            # Forward if needed
            if contract.id not in self.incoming_contracts:
                self.incoming_contracts[contract.id] = contract
                self.multicast_message(u'contract', {'contract': contract.to_dict()}, exclude=message.candidate)

    def send_block_request(self, block_id):
        self.request_cache.add(BlockRequestCache(self, block_id))
        candidate = next(self.dispersy.dispersy_yield_verified_candidates(), None)
        self.send_message(u'block-request', (candidate,), {'block_id': block_id})

    def on_block_request(self, messages):
        for message in messages:
            block_id = message.payload.dictionary['block_id']
            self.logger.debug('Got block-request for id %s', b64encode(block_id))

            block = self.data_manager.get_block(block_id)
            if block is not None:
                self.send_message(u'block', (message.candidate,), {'block': block.to_dict()})

    def on_block(self, messages):
        for message in messages:
            block = Block.from_dict(message.payload.dictionary['block'])
            if not block:
                self.logger.warning('Dropping invalid block from %s', message.candidate.sock_addr)
                continue

            # If we're trying to download this block, stop it. This needs to happen before any additional checks.
            # TODO: fix this
            for cache in self.request_cache._identifiers.values():
                if isinstance(cache, BlockRequestCache) and cache.block_id == block.id:
                    self.request_cache.pop(cache.prefix, cache.number)

            if not self.check_block(block):
                self.logger.warning('Dropping illegal block from %s', message.candidate.sock_addr)
                continue

            self.logger.debug('Got block %s', b64encode(block.id))

            # Are we dealing with an orphan block?
            if block.previous_hash != BLOCK_GENESIS_HASH and not self.data_manager.get_block(block.previous_hash):
                # Postpone processing the current block and request missing blocks
                self.incoming_blocks[block.id] = block
                # TODO: address issues with memory filling up
                self.send_block_request(block.previous_hash)
                self.logger.debug('Postpone block %s', b64encode(block.id))
                continue

            if self.process_block(block):
                self.logger.debug('Added received block with %s contract(s)', len(block.contracts))
                self.process_blocks_after(block)

    def process_blocks_after(self, block):
        # Process any orphan blocks that depend on the current block
        for orphan in self.incoming_blocks.values():
            if orphan.previous_hash == block.id:
                del self.incoming_blocks[orphan.id]
                if self.process_block(orphan):
                    self.logger.debug('Added postponed block with %s contract(s)', len(orphan.contracts))
                    self.process_blocks_after(orphan)

    def process_block(self, block):
        # We have already checked the proof of this block, but not whether the target_difficulty itself is as expected.
        # Note that we can't to this in check_block, because at that time the previous block may not be known yet.
        prev_block = self.data_manager.get_block(block.previous_hash)
        if block.target_difficulty != self.get_next_difficulty(prev_block):
            self.logger.debug('Block processing failed (unexpected target difficulty)')
            return False

        # Save block
        self.data_manager.add_block(block)

        # Get best chain
        latest_index = self.data_manager.get_block_indexes(limit=1)[0]

        # Calculate height of the chain this block is the head of
        block_ids = []
        from_height = 0
        cur_block = block
        while cur_block:
            block_ids.append(cur_block.id)
            block_index = self.data_manager.get_block_index(cur_block.previous_hash)
            if block_index is not None:
                # We can connect to the best chain
                from_height = block_index.height
                break
            cur_block = self.data_manager.get_block(cur_block.previous_hash)

        # Make sure that we are not dealing with a chain of orphan blocks
        if cur_block is None and block_ids[-1] != BLOCK_GENESIS_HASH:
            self.logger.error('Block processing failed (chain of orphan blocks)')
            return False

        # For now, the longest chain wins
        if len(block_ids) + from_height > latest_index.height:
            self.data_manager.remove_block_indexes(from_height + 1)
            for index, block_id in enumerate(reversed(block_ids)):
                self.data_manager.add_block_index(BlockIndex(block_id, from_height + 1 + index))

        # Make sure we stop trying to create blocks with the contracts in this block
        for contract in block.contracts:
            if contract.id in self.incoming_contracts:
                del self.incoming_contracts[contract.id]

        return True

    def check_block(self, block):
        if self.get_block_packet_size(block) > MAX_PACKET_SIZE:
            self.logger.debug('Block failed check (block too large)')
            return False

        if not self.check_proof(block):
            # Don't log message when we created the block
            if block.creator != self.my_user_id:
                self.logger.debug('Block failed check (incorrect proof)')
            return False

        if not block.verify():
            self.logger.debug('Block failed check (invalid signature)')
            return False

        if self.data_manager.get_block(block.id):
            self.logger.debug('Block failed check (duplicate block)')
            return False

        if block.time > int(time.time()) + MAX_CLOCK_DRIFT:
            self.logger.debug('Block failed check (max clock drift exceeded)')
            return False

        for contract in block.contracts:
            if block.time < contract.time:
                self.logger.debug('Block failed check (block created before contract)')
                return False

            if not self.check_contract(contract):
                self.logger.warning('Block check failed (contract check failed)')
                self.incoming_contracts.pop(contract.id, None)
                return False

        if len(block.contracts) != len(set([contract.id for contract in block.contracts])):
            self.logger.debug('Block failed check (duplicate contracts)')
            return False

        if block.merkle_root_hash != block.merkle_tree.build():
            self.logger.debug('Block failed check (incorrect merkle root hash)')
            return False

        past_blocks = self.get_past_blocks(block, 11)
        if past_blocks and block.time < median([b.time for b in past_blocks]):
            self.logger.debug('Block failed check (block time smaller than median time of past 11 blocks)')
            return False

        return True

    def check_proof(self, block):
        proof = hashlib.sha256(str(block)).digest()
        return full_to_uint256(proof) < block.target_difficulty

    def create_block(self):
        latest_index = self.data_manager.get_block_indexes(limit=1)[0]
        prev_block = self.data_manager.get_block(latest_index.block_id) if latest_index is not None else None

        block = Block()
        block.previous_hash = prev_block.id if prev_block is not None else BLOCK_GENESIS_HASH
        block.target_difficulty = self.get_next_difficulty(prev_block)
        block.time = int(time.time())

        # Placeholder information (for calculating packet size)
        block.merkle_root_hash = block.merkle_tree.build()
        block.sign(self.my_member)

        # Find dependencies
        contracts = []
        dependencies = defaultdict(list)
        for contract in self.incoming_contracts.itervalues():
            if contract.previous_hash:
                # Get the previous contract from memory or the database
                prev_contract = self.incoming_contracts.get(contract.previous_hash) or \
                                self.data_manager.get_contract(contract.previous_hash)
                on_blockchain = self.data_manager.contract_on_blockchain(prev_contract.id) if prev_contract else False
                # We need to wait until the previous contract is received and on the blockchain
                if prev_contract is None or not on_blockchain:
                    dependencies[contract.previous_hash].append(contract)
                    continue
            contracts.append(contract)

        # Add contracts to block
        while contracts:
            contract = contracts.pop(0)
            block.contracts.append(contract)
            if self.get_block_packet_size(block) > MAX_PACKET_SIZE:
                block.contracts.pop()
                break

            if contract.id in dependencies:
                # Put dependencies at the front of the list, so they will be processed in the next iterations
                for index, dependency in enumerate(dependencies[contract.id]):
                    contracts.insert(index, dependency)

        # Calculate final merkle root hash + sign block
        block.merkle_root_hash = block.merkle_tree.build()
        block.sign(self.my_member)

        if self.check_block(block):
            self.logger.debug('Created block with target difficulty 0x%064x', block.target_difficulty)
            if self.process_block(block):
                self.logger.debug('Added created block with %s contract(s)', len(block.contracts))
                self.multicast_message(u'block', {'block': block.to_dict()})

    def get_next_difficulty(self, block):
        # Determine difficulty for the next block
        if block is not None:
            target_difficulty = block.target_difficulty

            # Go back BLOCK_TARGET_BLOCKSPAN
            past_blocks = self.get_past_blocks(block, BLOCK_TARGET_BLOCKSPAN)
            if past_blocks:
                target_difficulty *= float(block.time - past_blocks[-1].time) / BLOCK_TARGET_TIMESPAN
        else:
            target_difficulty = BLOCK_DIFFICULTY_INIT

        target_difficulty = min(target_difficulty, BLOCK_DIFFICULTY_MIN)
        return compact_to_uint256(uint256_to_compact(target_difficulty))

    def get_past_blocks(self, block, num_past):
        result = []
        current = block
        for _ in range(num_past):
            current = self.data_manager.get_block(current.previous_hash)
            if current is None:
                return None
            result.append(current)
        return result

    def get_block_packet_size(self, block):
        meta = self.get_meta_message(u'block')
        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            destination=(Candidate(('1.1.1.1', 1), False),),
                            payload=({'block': block.to_dict()},))
        return len(message.packet)

    def check_contract(self, contract, fail_without_parent=True):
        if not contract.verify():
            self.logger.debug('Contract failed check (invalid signature)')
            return False

        if contract.previous_hash:
            prev_contract = self.incoming_contracts.get(contract.previous_hash) or \
                            self.data_manager.get_contract(contract.previous_hash) if contract.previous_hash else None

            if prev_contract is None:
                if fail_without_parent:
                    self.logger.error('Contract failed check (parent is unknown)')
                    return False
                else:
                    return True

        return True

    def begin_contract(self, candidate, document, contract_type, from_id, to_id, previous_hash=''):
        assert to_id == self.my_user_id or from_id == self.my_user_id

        contract = Contract()
        contract.from_id = from_id
        contract.to_id = to_id
        contract.document = document
        contract.type = contract_type
        contract.previous_hash = previous_hash
        contract.time = int(time.time())
        contract.sign(self.my_member)

        return self.send_signature_request(contract, candidate)

    def finalize_contract(self, contract, sign=False):
        # Final checks?

        if sign:
            contract.sign(self.my_member)

        # Add contract to database
        self.data_manager.add_contract(contract)

        return True

    def has_sibling(self, contract):
        for c in self.incoming_contracts.itervalues():
            if c.id != contract.id and c.previous_hash == contract.previous_hash:
                return True

        if self.data_manager.find_contracts(Contract.previous_hash == contract.previous_hash,
                                            Contract.id != contract.id).count() > 0:
            return True

        return False

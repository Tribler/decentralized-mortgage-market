import hashlib

from merkle import MerkleTree
from base64 import urlsafe_b64encode
from storm.properties import Int, RawStr
from storm.references import ReferenceSet
from storm.store import Store

from market.models.contract import Contract
from market.util.uint256 import bytes_to_uint256, uint256_to_bytes
from market.dispersy.crypto import LibNaCLPK


class Block(object):
    """
    This class represents a single block on the blockchain.
    """

    __storm_table__ = 'blockchain'
    _id = RawStr(name='id', primary=True)
    previous_hash = RawStr()
    merkle_root_hash = RawStr()
    creator = RawStr()
    creator_signature = RawStr()
    _target_difficulty = RawStr(name='target_difficulty')
    time = Int()
    _contracts = ReferenceSet(_id, Contract.block)

    def __init__(self):
        self.previous_hash = ''
        self.time = 0
        self.contracts = []

    def __storm_loaded__(self):
        self.contracts = []

    def __storm_pre_flush__(self):
        assert not self._id or self._id == self.id, 'Block.id has changed'
        self._id = self.id

        store = Store.of(self)
        for contract in self.contracts:
            if contract not in self._contracts:
                self._contracts.add(store.get(Contract, contract.id) or contract)

    def __str__(self):
        return '%s %s %s %s %d' % (self.previous_hash, self.merkle_root_hash, self.creator, self._target_difficulty, self.time)

    def sign(self, member):
        assert isinstance(member._ec, LibNaCLPK), 'Only supporting libnacl crypto for now'
        self.creator = member.public_key
        self.creator_signature = member.sign(str(self))

    def verify(self):
        try:
            data = str(self)
            key = LibNaCLPK(self.creator[10:])
            return key.verify(self.creator_signature, data) == data
        except ValueError:
            return False

    @property
    def id(self):
        return hashlib.sha256(str(self)).digest()

    @property
    def target_difficulty(self):
        return bytes_to_uint256(self._target_difficulty)

    @target_difficulty.setter
    def target_difficulty(self, value):
        # TODO: save _target_difficulty in Bitcoin compact format
        # https://bitcoin.stackexchange.com/questions/2924/how-to-calculate-new-bits-value
        self._target_difficulty = uint256_to_bytes(value)

    @property
    def merkle_tree(self):
        leaves = [contract.id for contract in self.contracts]
        if not leaves:
            leaves.append('\00' * 32)
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])
        return MerkleTree(leaves)

    def to_dict(self, api_response=False):
        return {
            'previous_hash': urlsafe_b64encode(self.previous_hash) if api_response else self.previous_hash,
            'merkle_root_hash': self.merkle_root_hash if api_response else self.merkle_root_hash,
            'creator': self.creator if api_response else self.creator,
            'creator_signature': self.creator_signature if api_response else self.creator_signature,
            'target_difficulty': self._target_difficulty if api_response else self._target_difficulty,
            'time': self.time,
            'contracts': [contract.to_dict() for contract in self.contracts]
        }

    @staticmethod
    def from_dict(block_dict):
        block = Block()
        block.previous_hash = block_dict['previous_hash']
        block.merkle_root_hash = block_dict['merkle_root_hash']
        block.creator = block_dict['creator']
        block.creator_signature = block_dict['creator_signature']
        block._target_difficulty = block_dict['target_difficulty']
        block.time = block_dict['time']
        block.contracts = [Contract.from_dict(contract_dict) for contract_dict in block_dict.get('contracts', [])]
        return block
import hashlib

from merkle import MerkleTree
from base64 import urlsafe_b64encode
from storm.properties import Int, RawStr
from storm.references import ReferenceSet
from storm.store import Store

from market.models.agreement import Agreement
from market.util.uint256 import bytes_to_uint256, uint256_to_bytes


class Block(object):
    """
    This class represents a single block on the blockchain.
    """

    __storm_table__ = 'blockchain'
    _id = RawStr(name='id', primary=True)
    previous_hash = RawStr()
    merkle_root_hash = RawStr()
    _target_difficulty = RawStr(name='target_difficulty')
    time = Int()
    _agreements = ReferenceSet(_id, Agreement.block)

    def __init__(self):
        self.previous_hash = ''
        self.merkle_root_hash = ''
        self.time = 0
        self.agreements = []

    def __storm_loaded__(self):
        self.agreements = []

    def __storm_pre_flush__(self):
        self.merkle_root_hash = self.merkle_tree().build()
        # TODO: fail if we already set the id and the hash has changed
        # Note that we need to calculate the merkle root hash before the id
        self._id = self.id

        store = Store.of(self)
        for agreement in self.agreements:
            if agreement not in self._agreements:
                self._agreements.add(store.get(Agreement, agreement.id) or agreement)

    def __str__(self):
        return '%s %s %s %d' % (self.previous_hash, self.merkle_root_hash, self._target_difficulty, self.time)

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

    def merkle_tree(self):
        return MerkleTree([agreement.id for agreement in self.agreements])

    def to_dict(self, api_response=False):
        return {
            'previous_hash': urlsafe_b64encode(self.previous_hash) if api_response else self.previous_hash,
            'merkle_root_hash': self.merkle_root_hash if api_response else self.merkle_root_hash,
            'target_difficulty': self._target_difficulty if api_response else self._target_difficulty,
            'time': self.time,
            'agreements': [agreement.to_dict() for agreement in self.agreements]
        }

    @staticmethod
    def from_dict(block_dict):
        block = Block()
        block.previous_hash = block_dict['previous_hash']
        block.merkle_root_hash = block_dict['merkle_root_hash']
        block._target_difficulty = block_dict['target_difficulty']
        block.time = block_dict['time']
        block.agreements = [Agreement.from_dict(agreement_dict) for agreement_dict in block_dict['agreements']]
        return block

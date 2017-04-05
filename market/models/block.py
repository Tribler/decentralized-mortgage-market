import hashlib

from storm.properties import Int, RawStr
from base64 import urlsafe_b64encode


class Block(object):
    """
    This class a single block on the blockchain.
    """

    __storm_table__ = "blockchain"
    id = Int(primary=True)
    signee = RawStr()
    document = RawStr()
    sequence_number_signee = Int()
    previous_hash_signee = RawStr()
    signature = RawStr()
    block_hash = RawStr()
    insert_time = Int()

    def __init__(self):
        self.signee = ''
        self.document = ''
        self.sequence_number_signee = 0
        self.previous_hash_signee = ''
        self.signature = ''
        self.block_hash = ''
        self.insert_time = 0

    def __str__(self):
        d = self.to_dict()
        d.pop('signature')
        return ';'.join(['%s=%s' % item for item in sorted(d.items())])

    def hash(self):
        self.block_hash = hashlib.sha256(str(self)).digest()

    def sign(self, member):
        self.signature = member.sign(str(self))

    def verify(self, member):
        return member.verify(str(self), self.signature)

    def to_dict(self, api_response=False):
        return {
            'signee': urlsafe_b64encode(self.signee) if api_response else self.signee,
            'document': urlsafe_b64encode(self.document) if api_response else self.document,
            'sequence_number_signee': self.sequence_number_signee,
            'previous_hash_signee': urlsafe_b64encode(self.previous_hash_signee) if api_response else self.previous_hash_signee,
            'signature': urlsafe_b64encode(self.signature) if api_response else self.signature
        }

    @staticmethod
    def from_dict(block_dict):
        block = Block()
        block.signee = block_dict['signee']
        block.document = block_dict['document']
        block.sequence_number_signee = block_dict['sequence_number_signee']
        block.previous_hash_signee = block_dict['previous_hash_signee']
        block.signature = block_dict['signature']
        return block

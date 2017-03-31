import hashlib

from storm.properties import Int, RawStr


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

    def to_dict(self):
        return {
            'signee': self.signee,
            'document': self.document,
            'sequence_number_signee': self.sequence_number_signee,
            'previous_hash_signee': self.previous_hash_signee,
            'signature': self.signature,
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

import time
import hashlib

from storm.properties import Int, RawStr


class Block(object):
    """
    This class a single block on the blockchain.
    """

    __storm_table__ = "blockchain"
    id = Int(primary=True)
    benefactor = RawStr()
    beneficiary = RawStr()
    agreement_benefactor = RawStr()
    agreement_beneficiary = RawStr()
    sequence_number_benefactor = Int()
    sequence_number_beneficiary = Int()
    previous_hash_benefactor = RawStr()
    previous_hash_beneficiary = RawStr()
    signature_benefactor = RawStr()
    signature_beneficiary = RawStr()
    insert_time = Int()
    hash_block = RawStr()
    previous_hash = RawStr()
    sequence_number = Int()

    def __init__(self, insert_time=int(time.time())):
        self.benefactor = ''
        self.beneficiary = ''
        self.agreement_benefactor = ''
        self.agreement_beneficiary = ''
        self.sequence_number_benefactor = 0
        self.sequence_number_beneficiary = 0
        self.previous_hash_benefactor = ''
        self.previous_hash_beneficiary = ''
        self.signature_benefactor = ''
        self.signature_beneficiary = ''
        self.insert_time = insert_time
        self.previous_hash = ''
        self.sequence_number = 0

    def __str__(self):
        d = self.to_dict()
        d.pop('signature_benefactor')
        d.pop('signature_beneficiary')
        return ';'.join(['%s=%s' % item for item in sorted(d.items())])

    def hash(self):
        self.hash_block = hashlib.sha256(str(self)).digest()

    def sign(self, member):
        sig = member.sign(str(self))
        if not self.signature_benefactor:
            self.signature_benefactor = sig
        else:
            self.signature_beneficiary = sig

    def verify(self, member):
        sig = self.signature_beneficiary or self.signature_benefactor
        return member.verify(str(self), sig)

    def to_dict(self):
        return {
            'benefactor': self.benefactor,
            'beneficiary': self.beneficiary,
            'agreement_benefactor': self.agreement_benefactor,
            'agreement_beneficiary': self.agreement_beneficiary,
            'sequence_number_benefactor': self.sequence_number_benefactor,
            'sequence_number_beneficiary': self.sequence_number_beneficiary,
            'previous_hash_benefactor': self.previous_hash_benefactor,
            'previous_hash_beneficiary': self.previous_hash_beneficiary,
            'signature_benefactor': self.signature_benefactor,
            'signature_beneficiary': self.signature_beneficiary
        }

    @staticmethod
    def from_dict(block_dict):
        block = Block()
        block.benefactor = block_dict['benefactor']
        block.beneficiary = block_dict['beneficiary']
        block.agreement_benefactor = block_dict['agreement_benefactor']
        block.agreement_beneficiary = block_dict['agreement_beneficiary']
        block.sequence_number_benefactor = block_dict['sequence_number_benefactor']
        block.sequence_number_beneficiary = block_dict['sequence_number_beneficiary']
        block.previous_hash_benefactor = block_dict['previous_hash_benefactor']
        block.previous_hash_beneficiary = block_dict['previous_hash_beneficiary']
        block.signature_benefactor = block_dict['signature_benefactor']
        block.signature_beneficiary = block_dict['signature_beneficiary']
        return block


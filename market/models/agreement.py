import hashlib

from base64 import urlsafe_b64encode
from storm.properties import Int, RawStr
from protobuf_to_dict import dict_to_protobuf

from market.community.market_pb2 import Agreement as AgreementPB


class Agreement(object):
    """
    This class represents an agreement between 2 users.
    """

    __storm_table__ = 'agreement'
    _id = RawStr(name='id', primary=True)
    previous_hash = RawStr()
    from_id = RawStr()
    from_signature = RawStr()
    to_id = RawStr()
    to_signature = RawStr()
    document = RawStr()
    block = RawStr()
    time = Int()

    def __init__(self):
        self.previous_hash = ''
        self.from_id = ''
        self.from_signature = ''
        self.to_id = ''
        self.to_signature = ''
        self.document = ''
        self.block = ''
        self.time = 0

    def __storm_pre_flush__(self):
        # TODO: fail if we already set the id and the hash has changed
        self._id = self.id

    def __str__(self):
        return '%s %s %d %s %s' % (self.from_id, self.to_id, self.time, self.previous_hash, self.document)

    @property
    def id(self):
        return hashlib.sha256(str(self)).digest()

    def sign(self, member):
        assert member.public_key in (self.from_id, self.to_id)

        if member.public_key == self.from_id:
            self.from_signature = member.sign(str(self))
        elif member.public_key == self.to_id:
            self.to_signature = member.sign(str(self))

    def verify(self, member):
        assert member.public_key in (self.from_id, self.to_id)

        if member.public_key == self.from_id:
            return member.verify(str(self), self.from_signature)
        elif member.public_key == self.to_id:
            return member.verify(str(self), self.to_signature)

    def to_bin(self):
        return dict_to_protobuf(AgreementPB, self.to_dict()).SerializeToString()

    def to_dict(self, api_response=False):
        return {
            'previous_hash': urlsafe_b64encode(self.previous_hash) if api_response else self.previous_hash,
            'from_id': urlsafe_b64encode(self.from_id) if api_response else self.from_id,
            'from_signature': urlsafe_b64encode(self.from_signature) if api_response else self.from_signature,
            'to_id': urlsafe_b64encode(self.to_id) if api_response else self.to_id,
            'to_signature': urlsafe_b64encode(self.to_signature) if api_response else self.to_signature,
            'document': urlsafe_b64encode(self.document) if api_response else self.document,
            'time': self.time
        }

    @staticmethod
    def from_dict(agreement_dict):
        agreement = Agreement()
        agreement.previous_hash = agreement_dict['previous_hash']
        agreement.from_id = agreement_dict['from_id']
        agreement.from_signature = agreement_dict['from_signature']
        agreement.to_id = agreement_dict['to_id']
        agreement.to_signature = agreement_dict['to_signature']
        agreement.document = agreement_dict['document']
        agreement.time = agreement_dict['time']
        return agreement

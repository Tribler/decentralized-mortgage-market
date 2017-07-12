from enum import IntEnum

from base64 import urlsafe_b64encode
from storm.properties import Int, Float, RawStr, Unicode
from protobuf_to_dict import dict_to_protobuf, protobuf_to_dict

from market.community.market.conversion_pb2 import Transfer as TransferPB
from market.database.types import Enum


class TransferStatus(IntEnum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class Transfer(object):
    """
    This class represents the change of ownership of an investment.
    """

    __storm_table__ = 'transfer'
    __storm_primary__ = 'id', 'user_id'
    id = Int()
    user_id = RawStr()
    iban = Unicode()
    amount = Float()
    investment_id = Int()
    investment_user_id = RawStr()
    status = Enum(TransferStatus)
    contract_id = RawStr()

    def __init__(self, identifier, user_id, iban, amount, investment_id, investment_user_id, status, contract_id=''):
        self.id = identifier
        self.user_id = user_id
        self.iban = iban
        self.amount = amount
        self.investment_id = investment_id
        self.investment_user_id = investment_user_id
        self.status = status
        self.contract_id = contract_id

    def to_dict(self, api_response=False):
        return {
            'id': self.id,
            'user_id': urlsafe_b64encode(self.user_id) if api_response else self.user_id,
            'iban': self.iban,
            'amount': self.amount,
            'investment_id': self.investment_id,
            'investment_user_id': urlsafe_b64encode(self.investment_user_id) if api_response else self.investment_user_id,
            'status': self.status.name if api_response else self.status.value,
            'contract_id': urlsafe_b64encode(self.contract_id) if api_response else self.contract_id
        }

    @staticmethod
    def from_dict(transfer_dict):
        try:
            status = TransferStatus(transfer_dict['status'])
        except ValueError:
            return None

        return Transfer(transfer_dict['id'],
                        transfer_dict['user_id'],
                        transfer_dict['iban'],
                        transfer_dict['amount'],
                        transfer_dict['investment_id'],
                        transfer_dict['investment_user_id'],
                        status,
                        transfer_dict['contract_id'])

    def to_bin(self):
        return dict_to_protobuf(TransferPB, self.to_dict()).SerializeToString()

    @staticmethod
    def from_bin(binary):
        msg = TransferPB()
        msg.ParseFromString(binary)
        return Transfer.from_dict(protobuf_to_dict(msg))

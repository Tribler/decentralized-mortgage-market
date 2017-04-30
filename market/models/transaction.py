from base64 import urlsafe_b64encode
from storm.properties import Int, Float, RawStr, Unicode
from protobuf_to_dict import dict_to_protobuf, protobuf_to_dict

from market.community.market_pb2 import Transaction as TransactionPB


class Transaction(object):
    """
    This class represents the change of ownership of an investment.
    """

    __storm_table__ = 'transaction'
    id = Int(primary=True)
    iban = Unicode()
    amount = Float()
    investment_id = RawStr()
    investment_user_id = RawStr

    def __init__(self, iban, amount, investment_id, investment_user_id, contract_id=''):
        self.iban = iban
        self.amount = amount
        self.investment_id = investment_id
        self.investment_user_id = investment_user_id
        self.contract_id = contract_id

    def to_dict(self, api_response=False):
        return {
            'iban': self.iban,
            'amount': self.amount,
            'investment_id': self.investment_id,
            'investment_user_id': urlsafe_b64encode(self.investment_user_id) if api_response else self.investment_user_id,
            'contract_id': urlsafe_b64encode(self.contract_id) if api_response else self.contract_id
        }

    @staticmethod
    def from_dict(transaction_dict):
        return Transaction(transaction_dict['iban'],
                           transaction_dict['amount'],
                           transaction_dict['investment_id'],
                           transaction_dict['investment_user_id'],
                           transaction_dict['contract_id'])

    def to_bin(self):
        return dict_to_protobuf(TransactionPB, self.to_dict()).SerializeToString()

    @staticmethod
    def from_bin(binary):
        msg = TransactionPB()
        msg.ParseFromString(binary)
        return Transaction.from_dict(protobuf_to_dict(msg))

from base64 import urlsafe_b64encode
from protobuf_to_dict import dict_to_protobuf, protobuf_to_dict
from storm.properties import Int, RawStr, Unicode, Float

from market.community.market.conversion_pb2 import Confirmation as ConfirmationPB


class Confirmation(object):
    """
    This class represents the payment confirmation related to a specific transfer.
    """

    __storm_table__ = 'confirmation'
    id = Int(primary=True)
    transfer_id = Int()
    transfer_user_id = RawStr()
    from_iban = Unicode()
    to_iban = Unicode()
    amount = Float()

    def __init__(self, transfer_id, transfer_user_id, from_iban, to_iban, amount):
        self.transfer_id = transfer_id
        self.transfer_user_id = transfer_user_id
        self.from_iban = from_iban
        self.to_iban = to_iban
        self.amount = amount

    def to_dict(self, api_response=False):
        return {
            'transfer_id': self.transfer_id,
            'transfer_user_id': urlsafe_b64encode(self.transfer_user_id) if api_response else self.transfer_user_id,
            'from_iban': self.from_iban,
            'to_iban': self.to_iban,
            'amount': self.amount
        }

    @staticmethod
    def from_dict(confirmation_dict):
        return Confirmation(confirmation_dict['transfer_id'],
                            confirmation_dict['transfer_user_id'],
                            confirmation_dict['from_iban'],
                            confirmation_dict['to_iban'],
                            confirmation_dict['amount'])

    def to_bin(self):
        return dict_to_protobuf(ConfirmationPB, self.to_dict()).SerializeToString()

    @staticmethod
    def from_bin(binary):
        msg = ConfirmationPB()
        msg.ParseFromString(binary)
        return Confirmation.from_dict(protobuf_to_dict(msg))

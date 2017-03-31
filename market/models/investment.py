from enum import Enum as PyEnum

from storm.properties import Int, Float, RawStr
from market.database.types import Enum
from base64 import urlsafe_b64encode
from market.community.market_pb2 import Investment as InvestmentPB
from protobuf_to_dict import dict_to_protobuf, protobuf_to_dict


class InvestmentStatus(PyEnum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class Investment(object):
    """
    This class represents an investment of someone in a specific campaign.
    """

    __storm_table__ = "investment"
    __storm_primary__ = "id", "user_id"
    id = Int()
    user_id = RawStr()
    amount = Float()
    duration = Int()
    interest_rate = Float()
    campaign_id = Int()
    campaign_user_id = RawStr()
    status = Enum(InvestmentStatus)

    def __init__(self, identifier, user_id, amount, duration, interest_rate, campaign_id, campaign_user_id, status):
        self.id = identifier
        self.user_id = user_id
        self.amount = amount
        self.duration = duration
        self.interest_rate = interest_rate
        self.campaign_id = campaign_id
        self.campaign_user_id = campaign_user_id
        self.status = status

    def to_dict(self, api_response=False):
        return {
            "id": self.id,
            "user_id": urlsafe_b64encode(self.user_id) if api_response else self.user_id,
            "amount": self.amount,
            "duration": self.duration,
            "interest_rate": self.interest_rate,
            "campaign_id": self.campaign_id,
            "campaign_user_id": urlsafe_b64encode(self.campaign_user_id) if api_response else self.campaign_user_id,
            "status": self.status.name if api_response else self.status.value
        }

    @staticmethod
    def from_dict(investment_dict):
        try:
            status = InvestmentStatus(investment_dict['status'])
        except ValueError:
            return None

        return Investment(investment_dict['id'],
                          investment_dict['user_id'],
                          investment_dict['amount'],
                          investment_dict['duration'],
                          investment_dict['interest_rate'],
                          investment_dict['campaign_id'],
                          investment_dict['campaign_user_id'],
                          status)

    def to_bin(self):
        return dict_to_protobuf(InvestmentPB, self.to_dict()).SerializeToString()

    @staticmethod
    def from_bin(self, binary):
        msg = InvestmentPB()
        msg.ParseFromString(binary)
        return Investment.from_dict(protobuf_to_dict(msg))

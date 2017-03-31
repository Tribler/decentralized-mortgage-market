from enum import Enum as PyEnum

from storm.properties import Int, Float, Unicode
from market.database.types import Enum


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
    id = Unicode(primary=True)
    user_id = Unicode()
    amount = Float()
    duration = Int()
    interest_rate = Float()
    campaign_id = Unicode()
    status = Enum(InvestmentStatus)

    def __init__(self, identifier, user_id, amount, duration, interest_rate, campaign_id, status):
        self.id = identifier
        self.user_id = user_id
        self.amount = amount
        self.duration = duration
        self.interest_rate = interest_rate
        self.campaign_id = campaign_id
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "duration": self.duration,
            "interest_rate": self.interest_rate,
            "campaign_id": self.campaign_id,
            "status": self.status.name
        }

    @staticmethod
    def from_dict(investment_dict):
        status = investment_dict['status']
        status = InvestmentStatus[status] if status in InvestmentStatus.__members__ else None

        if status is None:
            return None

        return Investment(investment_dict['id'],
                          investment_dict['user_id'],
                          investment_dict['amount'],
                          investment_dict['duration'],
                          investment_dict['interest_rate'],
                          investment_dict['campaign_id'],
                          status)

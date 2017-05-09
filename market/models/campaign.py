from base64 import urlsafe_b64encode
from storm.references import ReferenceSet
from storm.properties import Int, Float, RawStr

from market.models.investment import Investment


class Campaign(object):
    """
    This class represents a campaign for a specific mortgage.
    """

    __storm_table__ = "campaign"
    __storm_primary__ = "id", "user_id"
    id = Int()
    user_id = RawStr()
    mortgage_id = Int()
    mortgage_user_id = RawStr()
    amount = Float()
    amount_invested = Float()
    end_time = Int()
    investments = ReferenceSet((id, user_id), (Investment.campaign_id, Investment.campaign_user_id))

    def __init__(self, identifier, user_id, mortgage_id, mortgage_user_id, amount, amount_invested, end_time):
        self.id = identifier
        self.user_id = user_id
        self.mortgage_id = mortgage_id
        self.mortgage_user_id = mortgage_user_id
        self.amount = amount
        self.amount_invested = amount_invested
        self.end_time = end_time

    @property
    def completed(self):
        return self.amount_invested >= self.amount

    def to_dict(self, api_response=False):
        return {
            'id': self.id,
            'user_id': urlsafe_b64encode(self.user_id) if api_response else self.user_id,
            'mortgage_id': self.mortgage_id,
            'mortgage_user_id': urlsafe_b64encode(self.mortgage_user_id) if api_response else self.mortgage_user_id,
            'amount': self.amount,
            'amount_invested': self.amount_invested,
            'end_time': self.end_time
        }

    @staticmethod
    def from_dict(campaign_dict):
        return Campaign(campaign_dict['id'],
                        campaign_dict['user_id'],
                        campaign_dict['mortgage_id'],
                        campaign_dict['mortgage_user_id'],
                        campaign_dict['amount'],
                        campaign_dict['amount_invested'],
                        campaign_dict['end_time'])

from storm.properties import Int, Float, RawStr
from market.models.investment import Investment, InvestmentStatus
from storm.references import ReferenceSet
from base64 import urlsafe_b64encode


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
    end_time = Int()
    investments = ReferenceSet((id, user_id), (Investment.campaign_id, Investment.campaign_user_id))

    def __init__(self, identifier, user_id, mortgage_id, mortgage_user_id, amount, end_time, completed):
        self.id = identifier
        self.user_id = user_id
        self.mortgage_id = mortgage_id
        self.mortgage_user_id = mortgage_user_id
        self.amount = amount
        self.end_time = end_time

    @property
    def investment(self):
        return sum([investment.amount for investment in self.investments
                    if investment.status == InvestmentStatus.ACCEPTED])

    @property
    def completed(self):
        return self.investment >= self.amount

    def to_dict(self, api_response=False):
        investment_dict = {
            "id": self.id,
            "user_id": urlsafe_b64encode(self.user_id) if api_response else self.user_id,
            "mortgage_id": self.mortgage_id,
            "mortgage_user_id": urlsafe_b64encode(self.mortgage_user_id) if api_response else self.mortgage_user_id,
            "amount": self.amount,
            "end_time": self.end_time,
            "completed": self.completed
        }

        if api_response:
            investment_dict['investment'] = self.investment

        return investment_dict

    @staticmethod
    def from_dict(campaign_dict):
        return Campaign(campaign_dict['id'],
                        campaign_dict['user_id'],
                        campaign_dict['mortgage_id'],
                        campaign_dict['mortgage_user_id'],
                        campaign_dict['amount'],
                        campaign_dict['end_time'],
                        campaign_dict['completed'])

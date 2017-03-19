from storm.properties import Int, Float, Bool, Unicode
from market.models.investment import Investment, InvestmentStatus
from storm.references import ReferenceSet


class Campaign(object):
    """
    This class represents a campaign for a specific mortgage.
    """

    __storm_table__ = "campaign"
    id = Unicode(primary=True)
    user_id = Unicode()
    mortgage_id = Unicode()
    amount = Float()
    end_time = Int()
    completed = Bool()
    investments = ReferenceSet(id, Investment.campaign_id)

    def __init__(self, identifier, user_id, mortgage_id, amount, end_time, completed):
        self.id = identifier
        self.user_id = user_id
        self.mortgage_id = mortgage_id
        self.amount = amount
        self.end_time = end_time
        self.completed = completed

    def calc_investment(self):
        investment = sum([investment.amount for investment in self.investments
                          if investment.status == InvestmentStatus.ACCEPTED])
        if investment >= self.amount:
            self.completed = True
        return investment

    def to_dict(self, include_investment=False):
        investment_dict = {}

        if include_investment:
            # Calculate investment first, since it could affect completed
            investment_dict['investment'] = self.calc_investment()

        investment_dict.update({
            "id": self.id,
            "user_id": self.user_id,
            "mortgage_id": self.mortgage_id,
            "amount": self.amount,
            "end_time": self.end_time,
            "completed": self.completed
        })
        return investment_dict

    @staticmethod
    def from_dict(campaign_dict):
        return Campaign(campaign_dict['id'],
                        campaign_dict['user_id'],
                        campaign_dict['mortgage_id'],
                        campaign_dict['amount'],
                        campaign_dict['end_time'],
                        campaign_dict['completed'])

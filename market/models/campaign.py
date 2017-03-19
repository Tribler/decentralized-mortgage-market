from market.models.mortgage import Mortgage
from market.models.investment import InvestmentStatus


class Campaign(object):
    """
    This class represents a campaign for a specific mortgage.
    """

    def __init__(self, user_id, mortgage, amount, end_time, completed):
        self._user_id = user_id
        self._mortgage = mortgage
        self._amount = amount
        self._end_time = end_time
        self._completed = completed

    def calc_investment(self):
        investment = sum([investment.amount for investment in self._mortgage.investments
                          if investment.status == InvestmentStatus.ACCEPTED])
        if investment >= self._amount:
            self._completed = True
        return investment

    @property
    def user_id(self):
        return self._user_id

    @property
    def mortgage(self):
        return self._mortgage

    @property
    def amount(self):
        return self._amount

    @property
    def end_time(self):
        return self._end_time

    @property
    def completed(self):
        return self._completed

    def to_dict(self, include_investment=False):
        investment_dict = {}

        if include_investment:
            # Calculate investment first, since it could affect completed
            investment_dict['investment'] = self.calc_investment()

        investment_dict.update({
            "user_id": self._user_id,
            "mortgage": self._mortgage.to_dict(),
            "amount": self._amount,
            "end_time": self._end_time,
            "completed": self._completed
        })
        return investment_dict

    @staticmethod
    def from_dict(campaign_dict):
        mortgage = Mortgage.from_dict(campaign_dict['mortgage'])

        if mortgage is None:
            return None

        return Campaign(campaign_dict['user_id'],
                        mortgage,
                        campaign_dict['amount'],
                        campaign_dict['end_time'],
                        campaign_dict['completed'])

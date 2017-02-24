from enum import Enum


class MortgageStatus(Enum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class Mortgage(object):
    """
    This class represents a mortgage of a specific user. Each mortgage is tied to a house.
    """

    def __init__(self, user_id, house, bank, amount, mortgage_type, interest_rate, max_invest_rate, default_rate,
                 duration, risk, investors, status, campaign_id):
        self._user_id = user_id
        self._house = house
        self._bank = bank
        self._amount = amount
        self._mortgage_type = mortgage_type
        self._interest_rate = interest_rate
        self._max_invest_rate = max_invest_rate
        self._default_rate = default_rate
        self._duration = duration
        self._risk = risk
        self._investors = investors
        self._status = status
        self._campaign_id = campaign_id

    @property
    def id(self):
        return self._user_id + "_" + self._house.id

    @property
    def user_id(self):
        return self._user_id

    @property
    def house(self):
        return self._house

    @property
    def bank(self):
        return self._bank

    @property
    def amount(self):
        return self._amount

    @property
    def mortgage_type(self):
        return self._mortgage_type

    @property
    def interest_rate(self):
        return self._interest_rate

    @property
    def max_invest_rate(self):
        return self._max_invest_rate

    @property
    def default_rate(self):
        return self._default_rate

    @property
    def duration(self):
        return self._duration

    @property
    def risk(self):
        return self._risk

    @property
    def status(self):
        return self._status

    @property
    def investors(self):
        return self._investors

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def campaign_id(self):
        return self._campaign_id

    def to_dictionary(self):
        return {
            "user_id": self._user_id,
            "house_id": self.house.id,
            "bank": self._bank,
            "amount": self._amount,
            "mortgage_type": self._mortgage_type.name,
            "interest_rate": self._interest_rate,
            "max_invest_rate": self._max_invest_rate,
            "default_rate": self._default_rate,
            "duration": self._duration,
            "risk": self._risk,
            "status": self._status,
            "campaign_id": self._campaign_id
        }
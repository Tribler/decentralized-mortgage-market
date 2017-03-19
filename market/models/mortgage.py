from enum import Enum

from market.models.house import House


class MortgageStatus(Enum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class MortgageType(Enum):
    LINEAR = 0
    FIXEDRATE = 1


class Mortgage(object):
    """
    This class represents a mortgage of a specific user. Each mortgage is tied to a house.
    """

    def __init__(self, identifier, user_id, bank_id, house, amount, bank_amount, mortgage_type, interest_rate, max_invest_rate,
                 default_rate, duration, risk, status, campaign=None):
        self._id = identifier
        self._user_id = user_id
        self._bank_id = bank_id
        self._house = house
        self._amount = amount
        self._bank_amount = bank_amount
        self._mortgage_type = mortgage_type
        self._interest_rate = interest_rate
        self._max_invest_rate = max_invest_rate
        self._default_rate = default_rate
        self._duration = duration
        self._risk = risk
        self._investments = []
        self._status = status
        self._campaign = campaign

    @property
    def id(self):
        return self._id

    @property
    def user_id(self):
        return self._user_id

    @property
    def house(self):
        return self._house

    @property
    def bank_id(self):
        return self._bank_id

    @property
    def amount(self):
        return self._amount

    @property
    def bank_amount(self):
        return self._bank_amount

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
    def investments(self):
        return self._investments

    def get_investment(self, investment_id):
        for investment in self._investments:
            if investment.id == investment_id:
                return investment
        return None

    @status.setter
    def status(self, value):
        self._status = value

    @house.setter
    def house(self, value):
        self._house = value

    @property
    def campaign(self):
        return self._campaign

    def to_dict(self):
        return {
            "id": self._id,
            "user_id": self._user_id,
            "bank_id": self._bank_id,
            "house": self.house.to_dict(),
            "amount": self._amount,
            "bank_amount": self._bank_amount,
            "mortgage_type": self._mortgage_type.name,
            "interest_rate": self._interest_rate,
            "max_invest_rate": self._max_invest_rate,
            "default_rate": self._default_rate,
            "duration": self._duration,
            "risk": self._risk,
            "status": self._status.name,
        }

    @staticmethod
    def from_dict(mortgage_dict):
        house_dict = mortgage_dict['house']
        house = House.from_dict(house_dict)

        mortgage_type = mortgage_dict['mortgage_type']
        mortgage_type = MortgageType[mortgage_type] if mortgage_type in MortgageType.__members__ else None

        status = mortgage_dict['status']
        status = MortgageStatus[status] if status in MortgageStatus.__members__ else None

        if house is None or mortgage_type is None or status is None:
            return None

        return Mortgage(mortgage_dict['id'],
                        mortgage_dict['user_id'],
                        mortgage_dict['bank_id'],
                        house,
                        mortgage_dict['amount'],
                        mortgage_dict['bank_amount'],
                        mortgage_type,
                        mortgage_dict['interest_rate'],
                        mortgage_dict['max_invest_rate'],
                        mortgage_dict['default_rate'],
                        mortgage_dict['duration'],
                        mortgage_dict['risk'],
                        status)

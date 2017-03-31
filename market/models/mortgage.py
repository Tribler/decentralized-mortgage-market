from enum import Enum as PyEnum

from storm.base import Storm
from storm.properties import Int, Float, Unicode
from storm.references import Reference
from market.models.house import House
from market.database.types import Enum


class MortgageStatus(PyEnum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class MortgageType(PyEnum):
    LINEAR = 0
    FIXEDRATE = 1


# Mortgage inherits from Storm base class to prevent circular import issues with Campaign
class Mortgage(Storm):
    """
    This class represents a mortgage of a specific user. Each mortgage is tied to a house.
    """

    __storm_table__ = "mortgage"
    id = Unicode(primary=True)
    user_id = Unicode()
    bank_id = Unicode()
    house_id = Int()
    house = Reference(house_id, House.id)
    amount = Float()
    bank_amount = Float()
    mortgage_type = Enum(MortgageType)
    interest_rate = Float()
    max_invest_rate = Float()
    default_rate = Float()
    duration = Int()
    risk = Unicode()
    status = Enum(MortgageStatus)
    campaign_id = Unicode()
    campaign = Reference(campaign_id, 'Campaign.id')

    def __init__(self, identifier, user_id, bank_id, house, amount, bank_amount, mortgage_type, interest_rate, max_invest_rate,
                 default_rate, duration, risk, status, campaign=None):
        self.id = identifier
        self.user_id = user_id
        self.bank_id = bank_id
        self.house = house
        self.amount = amount
        self.bank_amount = bank_amount
        self.mortgage_type = mortgage_type
        self.interest_rate = interest_rate
        self.max_invest_rate = max_invest_rate
        self.default_rate = default_rate
        self.duration = duration
        self.risk = risk
        self.status = status
        # self.campaign = campaign

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bank_id": self.bank_id,
            "house": self.house.to_dict(),
            "amount": self.amount,
            "bank_amount": self.bank_amount,
            "mortgage_type": self.mortgage_type.name,
            "interest_rate": self.interest_rate,
            "max_invest_rate": self.max_invest_rate,
            "default_rate": self.default_rate,
            "duration": self.duration,
            "risk": self.risk,
            "status": self.status.name,
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

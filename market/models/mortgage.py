from enum import Enum as PyEnum

from storm.base import Storm
from storm.properties import Int, Float, Unicode, RawStr
from storm.references import Reference
from market.models.house import House
from market.database.types import Enum
from base64 import urlsafe_b64encode
from market.community.market_pb2 import Mortgage as MortgagePB
from protobuf_to_dict import dict_to_protobuf, protobuf_to_dict


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
    __storm_primary__ = "id", "user_id"
    id = Int()
    user_id = RawStr()
    bank_id = RawStr()
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

    def __init__(self, identifier, user_id, bank_id, house, amount, bank_amount, mortgage_type, interest_rate, max_invest_rate,
                 default_rate, duration, risk, status):
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

    def to_dict(self, api_response=False):
        return {
            "id": self.id,
            "user_id": urlsafe_b64encode(self.user_id) if api_response else self.user_id,
            "bank_id": urlsafe_b64encode(self.bank_id) if api_response else self.bank_id,
            "house": self.house.to_dict(),
            "amount": self.amount,
            "bank_amount": self.bank_amount,
            "mortgage_type": self.mortgage_type.name if api_response else self.mortgage_type.value,
            "interest_rate": self.interest_rate,
            "max_invest_rate": self.max_invest_rate,
            "default_rate": self.default_rate,
            "duration": self.duration,
            "risk": self.risk,
            "status": self.status.name if api_response else self.status.value
        }

    @staticmethod
    def from_dict(mortgage_dict):
        house_dict = mortgage_dict['house']
        house = House.from_dict(house_dict)

        if house is None:
            return None

        try:
            mortgage_type = MortgageType(mortgage_dict['mortgage_type'])
            status = MortgageStatus(mortgage_dict['status'])
        except ValueError:
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

    def to_bin(self):
        return dict_to_protobuf(MortgagePB, self.to_dict()).SerializeToString()

    @staticmethod
    def from_bin(self, binary):
        msg = MortgagePB()
        msg.ParseFromString(binary)
        return Mortgage.from_dict(protobuf_to_dict(msg))

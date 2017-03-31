from enum import Enum as PyEnum

from storm.properties import Float, Unicode, Int
from storm.references import Reference
from market.database.types import Enum
from market.models.house import House
from market.models.mortgage import MortgageType

class LoanRequestStatus(PyEnum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class LoanRequest(object):
    """
    This class represents a request for a loan.
    """

    __storm_table__ = "loan_request"
    id = Unicode(primary=True)
    user_id = Unicode()
    house_id = Int()
    house = Reference(house_id, House.id)
    mortgage_type = Enum(MortgageType)
    bank_id = Unicode()
    description = Unicode()
    amount_wanted = Float()
    status = Enum(LoanRequestStatus)

    def __init__(self, identifier, user_id, house, mortgage_type, bank_id, description, amount_wanted, status):
        self.id = identifier
        self.user_id = user_id
        self.house = house
        self.mortgage_type = mortgage_type
        self.bank_id = bank_id
        self.description = description
        self.amount_wanted = amount_wanted
        self.status = status


    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "house": self.house.to_dict(),
            "mortgage_type": self.mortgage_type.name,
            "bank_id": self.bank_id,
            "description": self.description,
            "amount_wanted": self.amount_wanted,
            "status": self.status.name
        }

    @staticmethod
    def from_dict(loan_request_dict):
        house_dict = loan_request_dict['house']
        house = House.from_dict(house_dict)

        mortgage_type = loan_request_dict['mortgage_type']
        mortgage_type = MortgageType[mortgage_type] if mortgage_type in MortgageType.__members__ else None

        status = loan_request_dict['status']
        status = LoanRequestStatus[status] if status in LoanRequestStatus.__members__ else None

        if house is None or mortgage_type is None or status is None:
            return None

        return LoanRequest(loan_request_dict['id'],
                           loan_request_dict['user_id'],
                           house,
                           mortgage_type,
                           loan_request_dict['bank_id'],
                           loan_request_dict['description'],
                           loan_request_dict['amount_wanted'],
                           status)

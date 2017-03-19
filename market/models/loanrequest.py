from enum import Enum

from market.models.house import House
from market.models.mortgage import MortgageType


class LoanRequestStatus(Enum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class LoanRequest(object):
    """
    This class represents a request for a loan.
    """

    def __init__(self, identifier, user_id, house, mortgage_type, bank_ids, description, amount_wanted, status):
        self._id = identifier
        self._user_id = user_id
        self._house = house
        self._mortgage_type = mortgage_type
        self._bank_ids = bank_ids
        self._description = description
        self._amount_wanted = amount_wanted
        self._status = status

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
    def mortgage_type(self):
        return self._mortgage_type

    @property
    def bank_ids(self):
        return self._bank_ids

    @property
    def description(self):
        return self._description

    @property
    def amount_wanted(self):
        return self._amount_wanted

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self._user_id,
            "house": self._house.to_dict(),
            "mortgage_type": self._mortgage_type.name,
            "bank_ids": self._bank_ids,
            "description": self._description,
            "amount_wanted": self._amount_wanted,
            "status": self._status.name
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
                           loan_request_dict['bank_ids'],
                           loan_request_dict['description'],
                           loan_request_dict['amount_wanted'],
                           status)

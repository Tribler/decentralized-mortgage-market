from enum import Enum


class LoanRequestStatus(Enum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class LoanRequest(object):
    """
    This class represents a request for a loan.
    """

    def __init__(self, user, house, mortgage_type, banks, description, amount_wanted, status):
        self._user = user
        self._house = house
        self._mortgage_type = mortgage_type
        self._banks = banks
        self._description = description
        self._amount_wanted = amount_wanted
        self._status = status

    @property
    def id(self):
        return self._user.id + "_" + self._house

    @property
    def user(self):
        return self._user

    @property
    def house(self):
        return self.house

    @property
    def mortgage_type(self):
        return self._mortgage_type

    @property
    def banks(self):
        return self._banks

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

    def to_dictionary(self):
        return {
            "id": self.id,
            "user_id": self._user.id,
            "house_id": self._house.id,
            "mortgage_type": self._mortgage_type.name,
            "banks": self._banks,
            "description": self._description,
            "amount_wanted": self._amount_wanted,
            "status": self._status
        }

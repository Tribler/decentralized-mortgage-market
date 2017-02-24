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

    def __init__(self, user_id, house_id, mortgage_type, banks, description, amount_wanted, status):
        self._user_id = user_id
        self._house_id = house_id
        self._mortgage_type = mortgage_type
        self._banks = banks
        self._description = description
        self._amount_wanted = amount_wanted
        self._status = status

    @property
    def user_id(self):
        return self._user_id

    @property
    def house_id(self):
        return self._house_id

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
            "user_id": self._user_id,
            "house_id": self._house_id,
            "mortgage_type": self._mortgage_type.name,
            "banks": self._banks,
            "description": self._description,
            "amount_wanted": self._amount_wanted,
            "status": self._status
        }

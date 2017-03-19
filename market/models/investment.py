from enum import Enum


class InvestmentStatus(Enum):
    NONE = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3


class Investment(object):
    """
    This class represents an investment of someone in a specific mortgage.
    """

    def __init__(self, identifier, user_id, amount, duration, interest_rate, mortgage_id, status):
        self._id = identifier
        self._user_id = user_id
        self._amount = amount
        self._duration = duration
        self._interest_rate = interest_rate
        self._mortgage_id = mortgage_id
        self._status = status

    @property
    def id(self):
        return self._id

    @property
    def user_id(self):
        return self._user_id

    @property
    def status(self):
        return self._status

    @property
    def amount(self):
        return self._amount

    @property
    def duration(self):
        return self._duration

    @property
    def interest_rate(self):
        return self._interest_rate

    @property
    def mortgage_id(self):
        return self._mortgage_id

    @status.setter
    def status(self, value):
        self._status = value

    def to_dict(self):
        return {
            "id": self._id,
            "user_id": self._user_id,
            "amount": self._amount,
            "duration": self._duration,
            "interest_rate": self._interest_rate,
            "mortgage_id": self._mortgage_id,
            "status": self._status.name
        }

    @staticmethod
    def from_dict(investment_dict):
        status = investment_dict['status']
        status = InvestmentStatus[status] if status in InvestmentStatus.__members__ else None

        if status is None:
            return None

        return Investment(investment_dict['id'],
                          investment_dict['user_id'],
                          investment_dict['amount'],
                          investment_dict['duration'],
                          investment_dict['interest_rate'],
                          investment_dict['mortgage_id'],
                          status)

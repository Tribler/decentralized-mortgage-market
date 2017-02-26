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

    def __init__(self, investor, amount, duration, interest_rate, mortgage, status):
        self._investor = investor
        self._amount = amount
        self._duration = duration
        self._interest_rate = interest_rate
        self._mortgage = mortgage
        self._status = status

    @property
    def investor(self):
        return self._investor

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
    def mortgage(self):
        return self._mortgage

    @status.setter
    def status(self, value):
        self._status = value

    def to_dictionary(self):
        return {
            "investor_id": self._investor.id,
            "amount": self._amount,
            "duration": self._duration,
            "interest_rate": self._interest_rate,
            "mortgage_id": self._mortgage.id,
            "status": self._status
        }

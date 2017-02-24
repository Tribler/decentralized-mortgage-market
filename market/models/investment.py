class Investment(object):
    """
    This class represents an investment of someone in a specific mortgage.
    """

    def __init__(self, investor_id, amount, duration, interest_rate, borrower_id, mortgage_id, status):
        self._investor_id = investor_id
        self._amount = amount
        self._duration = duration
        self._interest_rate = interest_rate
        self._borrower_id = borrower_id
        self._mortgage_id = mortgage_id
        self._status = status

    @property
    def investor_id(self):
        return self._investor_id

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
    def borrower_id(self):
        return self._borrower_id

    @property
    def mortgage_id(self):
        return self._mortgage_id

    @status.setter
    def status(self, value):
        self._status = value

    def to_dictionary(self):
        return {
            "investor_id": self._investor_id,
            "amount": self._amount,
            "duration": self._duration,
            "interest_rate": self._interest_rate,
            "borrower_id": self._borrower_id,
            "mortgage_id": self._mortgage_id,
            "status": self._status
        }

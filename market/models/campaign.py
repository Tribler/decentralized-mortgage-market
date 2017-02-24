class Campaign(object):
    """
    This class represents a campaign for a specific mortgage.
    """

    def __init__(self, user_id, mortgage_id, amount, end_date, completed):
        self._user_id = user_id
        self._mortgage_id = mortgage_id
        self._amount = amount
        self._end_date = end_date
        self._completed = completed

    def subtract_amount(self, investment):
        self._amount = self._amount - investment

        if self._amount <= 0:
            self._completed = True

    @property
    def mortgage_id(self):
        return self._mortgage_id

    @property
    def amount(self):
        return self._amount

    @property
    def end_date(self):
        return self._end_date

    @property
    def completed(self):
        return self._completed

    def to_dictionary(self):
        return {
            "user_id": self._user_id,
            "mortgage_id": self._mortgage_id,
            "amount": self._amount,
            "end_date": self._end_date,
            "completed": self._completed
        }

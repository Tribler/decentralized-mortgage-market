class Campaign(object):
    """
    This class represents a campaign for a specific mortgage.
    """

    def __init__(self, user, mortgage, amount, end_date, completed):
        self._user = user
        self._mortgage = mortgage
        self._amount = amount
        self._end_date = end_date
        self._completed = completed

    def subtract_amount(self, investment):
        self._amount = self._amount - investment

        if self._amount <= 0:
            self._completed = True

    @property
    def id(self):
        return self._mortgage.id

    @property
    def mortgage(self):
        return self._mortgage

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
            "id": self.id,
            "user_id": self._user.id,
            "mortgage": self._mortgage.to_dictionary(),
            "amount": self._amount,
            "end_date": self._end_date,
            "completed": self._completed
        }

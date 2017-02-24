import time

from enum import Enum

from market.dispersy.crypto import ECCrypto


class Role(Enum):
    NONE = 0
    BORROWER = 1
    INVESTOR = 2
    FINANCIAL_INSTITUTION = 3


class User(object):
    """
    This class represents a user in Dispersy.
    """

    @staticmethod
    def generate():
        crypto = ECCrypto()
        key = crypto.generate_key(u'high')
        public_bin = crypto.key_to_bin(key.pub())
        private_bin = crypto.key_to_bin(key)
        return User(public_key=public_bin.encode("hex"), private_key=private_bin.encode("hex"))

    def __init__(self, public_key, private_key=None, role=None, profile=None, loan_requests=None, campaigns=None,
                 mortgages=None, investments=None, time_added=time.time()):
        self._public_key = public_key
        self._private_key = private_key
        self._role = role
        self._profile = profile
        self._loan_requests = loan_requests or []
        self._campaigns = campaigns or []
        self._mortgages = mortgages or []
        self._investments = investments or []
        self._candidate = None
        self._time_added = time_added

    @property
    def id(self):
        return self._public_key

    @property
    def time_added(self):
        return self._time_added

    @property
    def profile(self):
        return self._profile

    @property
    def loan_requests(self):
        return self._loan_requests

    @property
    def mortgages(self):
        return self._mortgages

    @property
    def investments(self):
        return self._investments

    @property
    def role(self):
        return self._role

    @property
    def campaigns(self):
        return self._campaigns

    @profile.setter
    def profile(self, value):
        self._profile = value

    @role.setter
    def role(self, value):
        self._role = value

    def to_dictionary(self):
        return {
            "id": self._public_key,
            "role": self._role.name,
            "time_added": self._time_added
        }

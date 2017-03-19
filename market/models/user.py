from enum import Enum

from market.dispersy.crypto import ECCrypto


class Role(Enum):
    UNKNOWN = 0
    BORROWER = 1
    INVESTOR = 2
    FINANCIAL_INSTITUTION = 3


class User(object):
    """
    This class represents a user in Dispersy.
    """

    def __init__(self, public_key, private_key=None, role=None, profile=None):
        self._public_key = public_key
        self._private_key = private_key
        self._role = role
        self._profile = profile
        self._loan_requests = []
        self._campaigns = []
        self._mortgages = []
        self._investments = []
        self._candidate = None

    @property
    def id(self):
        return self._public_key

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
    def candidate(self):
        return self._candidate

    @property
    def campaigns(self):
        return self._campaigns

    @profile.setter
    def profile(self, value):
        self._profile = value

    @role.setter
    def role(self, value):
        self._role = value

    @candidate.setter
    def candidate(self, value):
        self._candidate = value

    def to_dict(self):
        return {
            "id": self._public_key,
            "role": self._role.name
        }

    @staticmethod
    def from_dict(user_dict):
        role = user_dict['role']
        role = Role[role] if role in Role.__members__ else None

        if role is None:
            return None

        return User(user_dict['id'], role=role)

    @staticmethod
    def generate():
        crypto = ECCrypto()
        key = crypto.generate_key(u'high')
        public_bin = crypto.key_to_bin(key.pub())
        private_bin = crypto.key_to_bin(key)
        return User(public_key=public_bin.encode("hex"), private_key=private_bin.encode("hex"))

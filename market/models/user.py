from enum import Enum as PyEnum

from storm.base import Storm
from storm.properties import Int, Unicode
from storm.references import ReferenceSet, Reference
from market.models.loanrequest import LoanRequest
from market.models.campaign import Campaign
from market.models.mortgage import Mortgage
from market.models.investment import Investment
from market.models.profile import Profile
from market.database.types import Enum


class Role(PyEnum):
    UNKNOWN = 0
    BORROWER = 1
    INVESTOR = 2
    FINANCIAL_INSTITUTION = 3


class User(Storm):
    """
    This class represents a user in Dispersy.
    """

    __storm_table__ = "user"
    id = Unicode(primary=True)
    role = Enum(Role)
    profile_id = Int()
    profile = Reference(profile_id, Profile.id)
    loan_requests = ReferenceSet(id, LoanRequest.user_id)
    campaigns = ReferenceSet(id, Campaign.user_id)
    mortgages = ReferenceSet(id, Mortgage.user_id)
    investments = ReferenceSet(id, Investment.user_id)

    def __init__(self, public_key, private_key=None, role=None):
        self.id = public_key
        self.private_key = private_key
        self.role = role

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role.name
        }

    @staticmethod
    def from_dict(user_dict):
        role = user_dict['role']
        role = Role[role] if role in Role.__members__ else None

        if role is None:
            return None

        return User(user_dict['id'], role=role)

from enum import Enum as PyEnum

from base64 import urlsafe_b64encode
from storm.base import Storm
from storm.properties import Int, RawStr
from storm.references import ReferenceSet, Reference

from market.models.loanrequest import LoanRequest
from market.models.campaign import Campaign
from market.models.mortgage import Mortgage
from market.models.investment import Investment
from market.models.transfer import Transfer
from market.models.profile import Profile
from market.database.types import Enum
from market.defs import VERIFIED_BANKS


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
    id = RawStr(primary=True)
    role = Enum(Role)
    profile_id = Int()
    profile = Reference(profile_id, Profile.id)
    loan_requests = ReferenceSet(id, LoanRequest.user_id)
    campaigns = ReferenceSet(id, Campaign.user_id)
    mortgages = ReferenceSet(id, Mortgage.user_id)
    investments = ReferenceSet(id, Investment.owner_id)
    transfers = ReferenceSet(id, Transfer.user_id)

    def __init__(self, public_key, private_key=None, role=None):
        self.id = public_key
        self.private_key = private_key
        self.role = role

    def to_dict(self, api_response=False):
        user_dict = {
            "id": urlsafe_b64encode(self.id) if api_response else self.id,
            "role": self.role.name if api_response else self.role.value
        }

        if api_response:
            bank_name = next((name for name, user_id in VERIFIED_BANKS.iteritems() if user_id == user_dict['id']), None)
            if bank_name is not None:
                user_dict['display_name'] = bank_name
            elif self.profile is not None:
                user_dict['display_name'] = '%s %s' % (self.profile.first_name, self.profile.last_name)

        return user_dict

    @staticmethod
    def from_dict(user_dict):
        try:
            role = Role(user_dict['role'])
        except ValueError:
            return None

        return User(user_dict['id'], role=role)

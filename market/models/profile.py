from storm.properties import Unicode, Int
from storm.references import Reference


class ProfileAddress(object):
    """
    This class represents address information, which borrowers are required to provide.
    """

    __storm_table__ = "profile_address"
    id = Int(primary=True)
    current_postal_code = Unicode()
    current_house_number = Unicode()
    current_address = Unicode()

    def __init__(self, current_postal_code, current_house_number, current_address):
        self.current_postal_code = current_postal_code
        self.current_house_number = current_house_number
        self.current_address = current_address

    def merge(self, other):
        for field_name in ('current_postal_code', 'current_house_number', 'current_address'):
            setattr(self, field_name, getattr(other, field_name))


class Profile(object):
    """
    This class represents an investor, someone who wants to lend money to users.
    """

    __storm_table__ = "profile"
    id = Int(primary=True)
    first_name = Unicode()
    last_name = Unicode()
    email = Unicode()
    iban = Unicode()
    phone_number = Unicode()
    address_id = Int()
    address = Reference(address_id, ProfileAddress.id)

    def __init__(self, first_name, last_name, email, iban, phone_number,
                 current_postal_code=None, current_house_number=None, current_address=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.iban = iban
        self.phone_number = phone_number

        if current_postal_code is not None and current_house_number is not None and current_address is not None:
            self.address = ProfileAddress(current_postal_code, current_house_number, current_address)

    def merge(self, other):
        for field_name in ('first_name', 'last_name', 'email', 'iban', 'phone_number'):
            setattr(self, field_name, getattr(other, field_name))

        if other.address is not None:
            if self.address is not None:
                self.address.merge(other.address)
            else:
                self.address = other.address

    def to_dict(self):
        profile_dict = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "iban": self.iban,
            "phone_number": self.phone_number,
        }

        if self.address is not None:
            profile_dict.update({
                "current_postal_code": self.address.current_postal_code,
                "current_house_number": self.address.current_house_number,
                "current_address": self.address.current_address
            })

        return profile_dict

    @staticmethod
    def from_dict(profile_dict):
        return Profile(profile_dict['first_name'],
                       profile_dict['last_name'],
                       profile_dict['email'],
                       profile_dict['iban'],
                       profile_dict['phone_number'],
                       profile_dict.get('current_postal_code'),
                       profile_dict.get('current_house_number'),
                       profile_dict.get('current_address'))

import time

from market.api.crypto import generate_key, get_public_key
from market.database.database import Database
from market.models.profiles import BorrowersProfile
from market.models.profiles import Profile
from market.models.role import Role
from market.models.user import User
from market.models.loans import Investment


class MarketAPI(object):
    def __init__(self, database):
        assert isinstance(database, Database)
        self._database = database
        self._user_key = None

    @property
    def db(self):
        return self._database

    @property
    def user_key(self):
        return self._user_key

    def create_user(self):
        """
        Create a new user and saves it to the database.
        :return: A tuple (User, public_key, private_key) or None if saving failed.
        """
        new_keys = generate_key()
        user = User(new_keys[0], time.time())  # Save the public key bin (encode as HEX) in the database along with the register time.

        if self.db.post(user.type, user):
            return user, new_keys[0], new_keys[1]
        else:
            return None

    def login_user(self, private_key):
        """
        Login a user by generating the public key from the private key and grabbing the user object using the generated key.
        :param public_key:
        :param private_key:
        :return:
        """
        if get_public_key(private_key):
            user = self.db.get('users', get_public_key(private_key))

            return user

    def create_profile(self, user, payload):
        """
        Creates a new profile and saves it to the database.
        :param user:
        :param payload:
        :return:
        """
        assert isinstance(user, User)
        assert isinstance(payload, dict)

        try:
            role = Role(user.id, payload['role'])
            user.role_id = self.db.post(role.type, role)

            profile = None
            if role.role_name == 'INVESTOR':
                profile = Profile(payload['first_name'], payload['last_name'], payload['email'], payload['iban'], payload['phonenumber'])
            elif role.role_name == 'BORROWER':
                profile = BorrowersProfile(payload['first_name'], payload['last_name'], payload['email'], payload['iban'],
                                           payload['phonenumber'], payload['current_postalcode'], payload['current_housenumber'], payload['documents_list'])
            else:
                return False

            user.profile_id = self.db.post(profile.type, profile)
            self.db.put(user.type, user.id, user)
            return profile
        except KeyError:
            return False

    def load_profile(self, user):
        """
        Get the profile from the database.
        :param user:
        :return:
        """
        role = self.db.get('role', user.role_id)

        profile = None
        if role.role_name == 'INVESTOR':
            profile = self.db.get('profile', user.profile_id)
        elif role.role_name == 'BORROWER':
            profile = self.db.get('borrowers_profile', user.profile_id)
        else:
            return False

        return profile

    def place_loan_offer(self, user, payload):
        """
        Create a loan offer and save it to the database.
        :param user:
        :param payload:
        :return:
        """
        assert isinstance(user, User)
        assert isinstance(payload, dict)

        try:
            role = Role(user.id, payload['role'])
            user.role_id = self.db.post(role.type, role)

            loan_offer = None
            if role.role_name == 'INVESTOR':
                loan_offer = Investment(payload['user_key'], payload['amount'], payload['duration'], payload['interest_rate'],
                                        payload['mortgage_id'], payload['status'])
            else:
                return False

            user.investment_ids.append(self.db.post('investment', loan_offer))
            self.db.put(user.type, user.id, user)
            return loan_offer
        except KeyError as e:
            print "KeyError: " + str(e)
            return False

    def resell_investment(self):
        """ post the data needed to resell the investment """
        pass

    def load_investments(self):
        """ get the data from current and pending investments """
        pass

    def load_open_market(self):
        """ get the 'to be displayed on the open market' data  """
        pass

    def browse_system(self):
        """ open a dialog window to browse the user's system (to upload their private key) """
        pass

    def remember_user(self):
        """ save the user's login credentials on their system """
        pass

    def generate_keys(self):
        """ generate a new key pair """
        pass

    def check_role(self):
        """ check which role the user has """
        pass

    def create_loan_request(self):
        """ create a new loan request """
        pass

    def load_borrowers_loans(self):
        """ display all of the borrower's current loans """
        pass

    def load_borrowers_offers(self):
        """ display all of the borrower's current offers """
        pass

    def accept_offer(self):
        """ accept an offer """
        pass

    def reject_offer(self):
        """ reject an offer """
        pass

    def load_all_loan_request(self, bank_id):
        """ load all pending loan requests for a specific bank """
        pass

    def load_single_loan_request(self, loan_request_id):
        """ load a specific loan request to """
        pass

    def accept_loan_request(self, loan_request_id):
        """ accept a pending loan request """
        pass

    def reject_loan_request(self, loan_request_id):
        """ reject a pending loan request """
        pass

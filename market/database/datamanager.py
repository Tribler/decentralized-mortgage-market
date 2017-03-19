from storm.database import create_database
from storm.store import Store

from market.models.user import User
from market.models.loanrequest import LoanRequest
from market.models.mortgage import Mortgage
from market.models.investment import Investment
from market.models.campaign import Campaign


class MarketDataManager:
    """
    This class stores and manages all the data for the decentralized mortgage market.
    """

    def __init__(self, market_db):
        self.database = create_database('sqlite:' + market_db)
        self.store = Store(self.database)

        self.store.execute("CREATE TABLE IF NOT EXISTS user (id VARCHAR PRIMARY KEY, role INT, profile_id INT)")
        self.store.execute("CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, address_id INT, "
                           "first_name VARCHAR, last_name VARCHAR, email VARCHAR, iban VARCHAR, phone_number VARCHAR)")
        self.store.execute("CREATE TABLE IF NOT EXISTS profile_address (id INTEGER PRIMARY KEY, "
                           "current_postal_code VARCHAR, current_house_number VARCHAR, current_address VARCHAR)")
        self.store.execute("CREATE TABLE IF NOT EXISTS loan_request (id VARCHAR PRIMARY KEY, user_id VARCHAR, "
                           "house_id INT, mortgage_type INT, bank_id VARCHAR, description VARCHAR, "
                           "amount_wanted FLOAT, status INT)")
        self.store.execute("CREATE TABLE IF NOT EXISTS house (id INTEGER PRIMARY KEY, "
                           "postal_code VARCHAR, house_number VARCHAR, address VARCHAR, price FLOAT, url VARCHAR, "
                           "seller_phone_number VARCHAR, seller_email VARCHAR)")
        self.store.execute("CREATE TABLE IF NOT EXISTS mortgage (id VARCHAR PRIMARY KEY, user_id VARCHAR, "
                           "bank_id VARCHAR, house_id INT, amount FLOAT, bank_amount FLOAT, mortgage_type INT, "
                           "interest_rate FLOAT, max_invest_rate FLOAT, default_rate FLOAT, duration INT, "
                           "risk VARCHAR, status INT, campaign_id VARCHAR)")
        self.store.execute("CREATE TABLE IF NOT EXISTS campaign (id VARCHAR PRIMARY KEY, user_id VARCHAR, "
                           "mortgage_id INT, amount FLOAT, end_time INT, completed INT)")
        self.store.execute("CREATE TABLE IF NOT EXISTS investment (id VARCHAR PRIMARY KEY, user_id VARCHAR, "
                           "amount FLOAT, duration INT, interest_rate FLOAT, campaign_id VARCHAR, status INT)")

        self.you = None

    def load_my_user(self, user_id, role):
        user = self.get_user(user_id)
        if user is None:
            user = User(user_id, role=role)
            self.add_user(user)
        self.you = user

    def add_user(self, user):
        self.store.add(user)

    def remove_user(self, user):
        self.store.remove(user)

    def get_user(self, user_id):
        return self.store.get(User, user_id)

    def get_users(self):
        return self.store.find(User)

    def get_loan_requests(self):
        """
        Get all loan requests in the market.
        :return: a list with LoanRequest objects
        """
        return self.store.find(LoanRequest)

    def get_loan_request(self, loan_request_id):
        """
        Get a loan requests in the market.
        :param loan_request_id: the of the loan request to search for
        :return: a LoanRequest object or None if no loan request could be found
        """
        return self.store.get(LoanRequest, loan_request_id)

    def get_mortgage(self, mortgage_id):
        """
        Get a specific mortgage with a specified id
        :param mortgage_id: the id of the mortgage to search for
        :return: a Mortgage object or None if no mortgage could be found
        """
        return self.store.get(Mortgage, mortgage_id)

    def get_investment(self, investment_id):
        """
        Get a specific investment with a specified id
        :param investment_id: the id of the investment to search for
        :return: an Investment object or None if no investment could be found
        """
        return self.store.get(Investment, investment_id)

    def get_campaign(self, campaign_id):
        """
        Get a specific campaign with a specified id
        :param campaign_id: the id of the campaign to search for
        :return: a Campaign object or None if no campaign could be found
        """
        return self.store.get(Campaign, campaign_id)

    def get_campaigns(self):
        """
        Get all campaigns in the market.
        :return: a list with Campaign objects
        """
        return self.store.find(Campaign)

    def flush(self):
        self.store.flush()

    def commit(self):
        self.store.commit()

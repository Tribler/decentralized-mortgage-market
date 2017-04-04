import os

from storm.database import create_database
from storm.store import Store

from market.models.user import User
from market.models.loanrequest import LoanRequest
from market.models.mortgage import Mortgage
from market.models.investment import Investment
from market.models.campaign import Campaign
from market.defs import BASE_DIR


class MarketDataManager:
    """
    This class stores and manages all the data for the decentralized mortgage market.
    """

    def __init__(self, market_db):
        self.database = create_database('sqlite:' + market_db)
        self.store = Store(self.database)

        with open(os.path.join(BASE_DIR, 'database', 'schema.sql')) as fp:
            schema = fp.read()
        for cmd in schema.split(';'):
            self.store.execute(cmd)

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

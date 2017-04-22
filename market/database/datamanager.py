import os

from storm.database import create_database
from storm.expr import Desc, Column

from market.models.user import User
from market.models.loanrequest import LoanRequest
from market.models.mortgage import Mortgage
from market.models.investment import Investment
from market.models.campaign import Campaign
from market.models.contract import Contract
from market.models.block import Block
from market.models.bestchain import BestChain
from market.database.store import MarketStore
from market.defs import BASE_DIR


class MarketDataManager:
    """
    This class stores and manages all the data for the decentralized mortgage market.
    """

    def __init__(self, market_db):
        self.database = create_database('sqlite:' + market_db)
        self.store = MarketStore(self.database)

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
        else:
            # Update role
            user.role = role
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

    def get_loan_request(self, loan_request_id, user_id):
        """
        Get a loan requests in the market.
        :param loan_request_id: the of the loan request to search for
        :param user_id: owner of the loan request
        :return: a LoanRequest object or None if no loan request could be found
        """
        return self.store.get(LoanRequest, (loan_request_id, user_id))

    def get_mortgage(self, mortgage_id, user_id):
        """
        Get a specific mortgage with a specified id
        :param mortgage_id: the id of the mortgage to search for
        :param user_id: owner of the mortgage
        :return: a Mortgage object or None if no mortgage could be found
        """
        return self.store.get(Mortgage, (mortgage_id, user_id))

    def get_mortgages(self):
        """
        Get all mortgages in the market.
        :return: a list with Mortgage objects
        """
        return self.store.find(Mortgage)

    def get_investment(self, investment_id, user_id):
        """
        Get a specific investment with a specified id
        :param investment_id: the id of the investment to search for
        :param user_id: owner of the investment
        :return: an Investment object or None if no investment could be found
        """
        return self.store.get(Investment, (investment_id, user_id))

    def get_campaign(self, campaign_id, user_id):
        """
        Get a specific campaign with a specified id
        :param campaign_id: the id of the campaign to search for
        :param user_id: owner of the campaign
        :return: a Campaign object or None if no campaign could be found
        """
        return self.store.get(Campaign, (campaign_id, user_id))

    def get_campaigns(self):
        """
        Get all campaigns in the market.
        :return: a list with Campaign objects
        """
        return self.store.find(Campaign)

    def add_contract(self, contract):
        self.store.add(contract)

    def get_contract(self, contract_id):
        self.store.get(Contract, contract_id)

    def add_block(self, block):
        self.store.add(block)

    def get_block(self, block_id):
        return self.store.get(Block, block_id)

    def get_blocks(self):
        """
        Get all blocks in the market.
        :return: a list with Block objects
        """
        return self.store.find(Block)

    def get_latest_block(self):
        """
        Get the latest Block from the blochchain.
        :return: the latest Block
        """
        return self.store.find(Block).order_by(Desc(Column('rowid'))).config(limit=1).one()

    def get_best_chain(self):
        best_chain = self.store.get(BestChain, 0)
        if best_chain is None:
            from market.community.community import BLOCK_GENESIS_HASH
            best_chain = BestChain(BLOCK_GENESIS_HASH, 0, 0)
            self.store.add(best_chain)
        return best_chain

    def flush(self):
        self.store.flush()

    def commit(self):
        self.store.commit()

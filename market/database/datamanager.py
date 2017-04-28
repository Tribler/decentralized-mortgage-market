import os

from storm.database import create_database
from storm.expr import Desc

from market.models.user import User
from market.models.loanrequest import LoanRequest
from market.models.mortgage import Mortgage
from market.models.investment import Investment
from market.models.campaign import Campaign
from market.models.contract import Contract
from market.models.block import Block
from market.models.block_index import BlockIndex
from market.models.block_contract import BlockContract
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

    def initialize(self, user_id, role):
        # Load or create local user
        user = self.get_user(user_id)
        if user is None:
            user = User(user_id, role=role)
            self.add_user(user)
        else:
            # Update role
            user.role = role
        self.you = user

        # Ensure we have a BlockIndex with height 0
        if self.get_block_indexes(limit=1).count() == 0:
            from market.community.community import BLOCK_GENESIS_HASH
            self.add_block_index(BlockIndex(BLOCK_GENESIS_HASH, 0))

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

    def get_mortgage_for_investment(self, investment):
        return self.store.find(Mortgage, Mortgage.id == Campaign.mortgage_id,
                               Mortgage.user_id == Campaign.mortgage_user_id,
                               investment.campaign_id == Campaign.id,
                               investment.campaign_user_id == Campaign.user_id).one()

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

    def get_campaign_for_mortgage(self, mortgage):
        return self.store.find(Campaign, Campaign.mortgage_id == mortgage.id,
                               Campaign.mortgage_user_id == mortgage.user_id).one()

    def get_campaigns(self):
        """
        Get all campaigns in the market.
        :return: a list with Campaign objects
        """
        return self.store.find(Campaign)

    def add_contract(self, contract):
        self.store.add(contract)

    def get_contract(self, contract_id):
        return self.store.get(Contract, contract_id)

    def find_contracts(self, *args):
        return self.store.find(Contract, *args)

    def contract_on_blockchain(self, contract_id):
        # Find blocks that contain this contract
        block_ids = []
        block_contracts = self.store.find(BlockContract, BlockContract.contract_id == contract_id)
        if block_contracts:
            for block_contract in block_contracts:
                block_ids.append(block_contract.block_id)

        # Find out if any of the blocks are on the best chain
        for block_id in block_ids:
            if self.get_block_index(block_id):
                return True
        return False

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

    def add_block_index(self, block_index):
        self.store.add(block_index)

    def get_block_index(self, block_id):
        return self.store.get(BlockIndex, block_id)

    def get_block_indexes(self, limit=500):
        return self.store.find(BlockIndex).order_by(Desc(BlockIndex.height)).config(limit=500)

    def remove_block_indexes(self, from_height):
        self.store.find(BlockIndex, BlockIndex.height >= from_height).remove()

    def flush(self):
        self.store.flush()

    def commit(self):
        self.store.commit()

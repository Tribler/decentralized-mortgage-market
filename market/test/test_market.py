import sys
import unittest

from twisted.internet.defer import inlineCallbacks

from market.community.market.community import MarketCommunity
from market.models.user import Role
from market.models.profile import Profile
from market.models.loanrequest import LoanRequest, LoanRequestStatus
from market.models.house import House
from market.models.mortgage import MortgageType, MortgageStatus, Mortgage
from market.dispersy.util import blocking_call_on_reactor_thread
from market.models.investment import Investment, InvestmentStatus
from market.models.campaign import Campaign
from market.models.transfer import TransferStatus, Transfer
from market.test.testcommunity import TestCommunity


class TestMarketCommunity(TestCommunity):

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def setUp(self):
        super(TestMarketCommunity, self).setUp()

        # Create communities
        self.node1 = self.create_community(role=Role.BORROWER)
        self.node2 = self.create_community(role=Role.FINANCIAL_INSTITUTION)

        # Take a step (i.e., send and receive an introduction-request)
        self.node1.take_step()

        # Wait until both nodes receive a user message
        yield self.get_next_message(self.node1, u'user')
        yield self.get_next_message(self.node2, u'user')

    @blocking_call_on_reactor_thread
    def test_user_introduction(self):
        self.assertEqual(self.node1.data_manager.get_user(self.node2.my_user_id).to_dict(), self.node2.my_user.to_dict())
        self.assertEqual(self.node2.data_manager.get_user(self.node1.my_user_id).to_dict(), self.node1.my_user.to_dict())

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_mortgage_agreement_successful(self):
        # Create loan request for which to send an offer
        loan_request = self.create_loan_request(self.node1, self.node1.my_user_id, self.node2.my_user_id)

        # Send loan request offer
        self.node1.offer_loan_request(loan_request)

        # Wait until offer is processed
        yield self.get_next_message(self.node2, u'offer')
        self.assertEqual(self.node2.data_manager.get_loan_request(loan_request.id, loan_request.user_id).to_dict(), loan_request.to_dict())

        # Create mortgage for which to send an offer
        mortgage = self.create_mortgage(self.node2, loan_request)

        # Send mortgage offer
        self.node2.offer_mortgage(loan_request, mortgage)

        # Wait until offer is processed
        yield self.get_next_message(self.node1, u'offer')
        self.assertEqual(self.node1.data_manager.get_mortgage(mortgage.id, mortgage.user_id).to_dict(), mortgage.to_dict())

        # Make sure we have the mortgage from the database of node1
        mortgage = self.node1.data_manager.get_mortgage(mortgage.id, mortgage.user_id)

        # Accept mortgage offer
        self.node1.accept_mortgage(mortgage)

        # Wait until accept is processed
        yield self.get_next_message(self.node2, u'accept')
        self.assertEqual(self.node2.data_manager.get_mortgage(mortgage.id, mortgage.user_id).status, MortgageStatus.ACCEPTED)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_mortgage_agreement_reject_loan_request(self):
        # Create loan request for which to send an offer
        loan_request = self.create_loan_request(self.node1, self.node1.my_user_id, self.node2.my_user_id)

        # Send loan request offer
        self.node1.offer_loan_request(loan_request)

        # Wait until offer is processed
        yield self.get_next_message(self.node2, u'offer')
        self.assertEqual(self.node2.data_manager.get_loan_request(loan_request.id, loan_request.user_id).to_dict(), loan_request.to_dict())

        # Send loan request reject
        self.node2.reject_loan_request(loan_request)

        # Wait until reject is processed
        yield self.get_next_message(self.node1, u'reject')
        self.assertEqual(loan_request.status, LoanRequestStatus.REJECTED)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_mortgage_agreement_reject_mortgage(self):
        # Create loan request for which to send an offer
        loan_request = self.create_loan_request(self.node1, self.node1.my_user_id, self.node2.my_user_id)

        # Send loan request offer
        self.node1.offer_loan_request(loan_request)

        # Wait until offer is processed
        yield self.get_next_message(self.node2, u'offer')
        self.assertEqual(self.node2.data_manager.get_loan_request(loan_request.id, loan_request.user_id).to_dict(), loan_request.to_dict())

        # Create mortgage for which to send an offer
        mortgage = self.create_mortgage(self.node2, loan_request)

        # Send mortgage offer
        self.node2.offer_mortgage(loan_request, mortgage)

        # Wait until offer is processed
        yield self.get_next_message(self.node1, u'offer')
        self.assertEqual(self.node1.data_manager.get_mortgage(mortgage.id, mortgage.user_id).to_dict(), mortgage.to_dict())

        # Make sure we have the mortgage from the database of node1
        mortgage = self.node1.data_manager.get_mortgage(mortgage.id, mortgage.user_id)

        # Accept mortgage offer
        self.node1.reject_mortgage(mortgage)

        # Wait until reject is processed
        yield self.get_next_message(self.node2, u'reject')
        self.assertEqual(self.node2.data_manager.get_mortgage(mortgage.id, mortgage.user_id).status, MortgageStatus.REJECTED)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_investment_agreement_successful(self):
        # Add some dummy data
        loan_request1 = self.create_loan_request(self.node1, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)
        loan_request2 = self.create_loan_request(self.node2, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)

        mortgage1 = self.create_mortgage(self.node1, loan_request1, status=MortgageStatus.ACCEPTED)
        mortgage2 = self.create_mortgage(self.node2, loan_request2, status=MortgageStatus.ACCEPTED)

        campaign1 = self.create_campaign(self.node1, mortgage1)
        self.create_campaign(self.node2, mortgage2)

        # Create and send an investment offer
        investment1 = self.create_investment(self.node1, self.node1.my_user_id, campaign1)
        self.node1.offer_investment(investment1)

        # Make sure we received the offer
        yield self.get_next_message(self.node2, u'offer')
        investment2 = self.node2.data_manager.get_investment(investment1.id, investment1.user_id)
        self.assertEqual(investment2.status, InvestmentStatus.PENDING)
        self.assertEqual(investment2.to_dict(), investment1.to_dict())

        # Accept offer
        # TODO: move this to accept_investment
        investment2.status = InvestmentStatus.ACCEPTED
        self.node2.accept_investment(investment2)

        # Check offer status
        yield self.get_next_message(self.node1, u'accept')
        self.assertEqual(investment1.status, InvestmentStatus.ACCEPTED)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_investment_agreement_reject(self):
        # Add some dummy data
        loan_request1 = self.create_loan_request(self.node1, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)
        loan_request2 = self.create_loan_request(self.node2, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)

        mortgage1 = self.create_mortgage(self.node1, loan_request1, status=MortgageStatus.ACCEPTED)
        mortgage2 = self.create_mortgage(self.node2, loan_request2, status=MortgageStatus.ACCEPTED)

        campaign1 = self.create_campaign(self.node1, mortgage1)
        self.create_campaign(self.node2, mortgage2)

        # Create and send an investment offer
        investment1 = self.create_investment(self.node1, self.node1.my_user_id, campaign1)
        self.node1.offer_investment(investment1)

        # Make sure we received the offer
        yield self.get_next_message(self.node2, u'offer')
        investment2 = self.node2.data_manager.get_investment(investment1.id, investment1.user_id)
        self.assertEqual(investment2.status, InvestmentStatus.PENDING)
        self.assertEqual(investment2.to_dict(), investment1.to_dict())

        # Reject offer
        # TODO: move this to accept_investment
        investment2.status = InvestmentStatus.REJECTED
        self.node2.reject_investment(investment2)

        # Check offer status
        yield self.get_next_message(self.node1, u'reject')
        self.assertEqual(investment1.status, InvestmentStatus.REJECTED)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_investment_agreement_auto_reject(self):
        # Add some dummy data
        loan_request1 = self.create_loan_request(self.node1, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)
        loan_request2 = self.create_loan_request(self.node2, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)

        mortgage1 = self.create_mortgage(self.node1, loan_request1, status=MortgageStatus.ACCEPTED)
        mortgage2 = self.create_mortgage(self.node2, loan_request2, status=MortgageStatus.ACCEPTED)

        campaign1 = self.create_campaign(self.node1, mortgage1)
        self.create_campaign(self.node2, mortgage2)

        # Create and send an investment offer
        investment1 = self.create_investment(self.node1, self.node1.my_user_id, campaign1)
        # Intentionally try to create an investment higher then allowed
        investment1.amount = 1000000
        self.node1.offer_investment(investment1)

        # Make sure we received the offer
        yield self.get_next_message(self.node2, u'offer')
        self.assertEqual(self.node2.data_manager.get_investment(investment1.id, investment1.user_id), None)

        # Check offer status (should be auto-rejected)
        yield self.get_next_message(self.node1, u'reject')
        self.assertEqual(investment1.status, InvestmentStatus.REJECTED)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_transfer_agreement_successful(self):
        # Add some dummy data
        loan_request1 = self.create_loan_request(self.node1, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)
        loan_request2 = self.create_loan_request(self.node2, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)

        mortgage1 = self.create_mortgage(self.node1, loan_request1, status=MortgageStatus.ACCEPTED)
        mortgage2 = self.create_mortgage(self.node2, loan_request2, status=MortgageStatus.ACCEPTED)

        campaign1 = self.create_campaign(self.node1, mortgage1)
        campaign2 = self.create_campaign(self.node2, mortgage2)

        investment1 = self.create_investment(self.node1, self.node2.my_user_id, campaign1, status=InvestmentStatus.FORSALE)
        self.create_investment(self.node2, self.node2.my_user_id, campaign2, status=InvestmentStatus.FORSALE)

        # Create and send an transfer offer
        transfer1 = self.create_transfer(self.node1, self.node1.my_user_id, investment1, status=TransferStatus.PENDING)
        # Bypass owner verification for now (owner contract must be on the blockchain first)
        self.node1.on_owner_verified(self.node2.my_member.public_key, transfer1, investment1)

        # Make sure we received the offer
        yield self.get_next_message(self.node2, u'offer')
        transfer2 = self.node1.data_manager.get_transfer(transfer1.id, transfer1.user_id)
        self.assertEqual(transfer1.to_dict(), transfer2.to_dict())

        # Accept offer
        self.node2.accept_transfer(transfer2)

        # Check status
        yield self.get_next_message(self.node1, u'accept')
        self.assertEqual(transfer1.status, TransferStatus.ACCEPTED)

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def test_transfer_agreement_reject(self):
        # Add some dummy data
        loan_request1 = self.create_loan_request(self.node1, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)
        loan_request2 = self.create_loan_request(self.node2, self.node1.my_user_id, self.node2.my_user_id, status=LoanRequestStatus.ACCEPTED)

        mortgage1 = self.create_mortgage(self.node1, loan_request1, status=MortgageStatus.ACCEPTED)
        mortgage2 = self.create_mortgage(self.node2, loan_request2, status=MortgageStatus.ACCEPTED)

        campaign1 = self.create_campaign(self.node1, mortgage1)
        campaign2 = self.create_campaign(self.node2, mortgage2)

        investment1 = self.create_investment(self.node1, self.node2.my_user_id, campaign1, status=InvestmentStatus.FORSALE)
        self.create_investment(self.node2, self.node2.my_user_id, campaign2, status=InvestmentStatus.FORSALE)

        # Create and send an transfer offer
        transfer1 = self.create_transfer(self.node1, self.node1.my_user_id, investment1, status=TransferStatus.PENDING)
        # Bypass owner verification for now (owner contract must be on the blockchain first)
        self.node1.on_owner_verified(self.node2.my_member.public_key, transfer1, investment1)

        # Make sure we received the offer
        yield self.get_next_message(self.node2, u'offer')
        transfer2 = self.node1.data_manager.get_transfer(transfer1.id, transfer1.user_id)
        self.assertEqual(transfer1.to_dict(), transfer2.to_dict())

        # Reject offer
        self.node2.reject_transfer(transfer2)

        # Check status
        yield self.get_next_message(self.node1, u'reject')
        self.assertEqual(transfer1.status, TransferStatus.REJECTED)

    def create_loan_request(self, community, user_id, bank_id, status=LoanRequestStatus.PENDING):
        user = community.data_manager.get_user(user_id)

        loan_request = LoanRequest(user.loan_requests.count(),
                                   user_id,
                                   House(u'1234AA', u'1', u'address', 100000, u'', u'1234567890', u'seller@example.org'),
                                   MortgageType.FIXEDRATE,
                                   bank_id,
                                   u'description',
                                   100000,
                                   status)
        user.loan_requests.add(loan_request)
        return loan_request

    def create_mortgage(self, community, loan_request, status=MortgageStatus.PENDING):
        user = community.data_manager.get_user(loan_request.user_id)

        # Make sure we have the loan request from the target community's database
        loan_request = community.data_manager.get_loan_request(loan_request.id, loan_request.user_id)

        mortgage = Mortgage(user.mortgages.count(),
                            loan_request.user_id,
                            loan_request.bank_id,
                            loan_request.house,
                            loan_request.amount_wanted,
                            loan_request.amount_wanted * 0.5,
                            loan_request.mortgage_type,
                            0.02,
                            0.02,
                            0.02,
                            12,
                            u'',
                            MortgageStatus.PENDING,
                            loan_request.id,
                            loan_request.user_id)
        user.mortgages.add(mortgage)
        return mortgage

    def create_campaign(self, community, mortgage):
        user = community.data_manager.get_user(mortgage.bank_id)

        campaign = Campaign(user.campaigns.count(),
                            mortgage.bank_id,
                            mortgage.id,
                            mortgage.user_id,
                            mortgage.amount * 0.5,
                            0,
                            sys.maxint)
        user.campaigns.add(campaign)
        return campaign

    def create_investment(self, community, user_id, campaign, status=InvestmentStatus.PENDING):
        user = community.data_manager.get_user(user_id)

        investment = Investment(user.investments.count(),
                                user.id,
                                10000,
                                0,
                                0.02,
                                campaign.id,
                                campaign.user_id,
                                status)
        user.investments.add(investment)
        return investment

    def create_transfer(self, community, user_id, investment, status=TransferStatus.PENDING):
        user = community.data_manager.get_user(user_id)

        transfer = Transfer(user.transfers.count(),
                            user.id,
                            u'IBAN1234567890',
                            10000,
                            investment.id,
                            investment.user_id,
                            status)
        user.transfers.add(transfer)
        return transfer

    def create_community(self, role=Role.UNKNOWN):
        community = super(TestMarketCommunity, self).create_community(MarketCommunity)
        community.data_manager.you.role = role
        community.my_user.profile = Profile(u'Firstname', u'Lastname', u'name@example.com', u'NL28RABO123456789', u'0123456789')
        # Disable blockchain
        community.begin_contract = lambda *args, **kwargs: None
        return community


if __name__ == "__main__":
    unittest.main()

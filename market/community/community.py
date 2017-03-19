import time
import logging

from twisted.internet.defer import inlineCallbacks

from market.api.datamanager import MarketDataManager
from market.community.conversion import MarketConversion
from market.community.payload import ProtobufPayload
from market.dispersy.authentication import MemberAuthentication
from market.dispersy.community import Community
from market.dispersy.conversion import DefaultConversion
from market.dispersy.destination import CommunityDestination, CandidateDestination
from market.dispersy.distribution import DirectDistribution, FullSyncDistribution
from market.dispersy.message import Message
from market.dispersy.resolution import PublicResolution
from market.models.loanrequest import LoanRequest, LoanRequestStatus
from market.models.mortgage import Mortgage, MortgageStatus
from market.models.profile import InvestorProfile, BorrowersProfile
from market.models.user import User, Role
from market.restapi.rest_manager import RESTManager
from market.models.campaign import Campaign
from market.models.investment import InvestmentStatus, Investment
from market.models import investment


class MarketCommunity(Community):

    def __init__(self, dispersy, master, my_member):
        super(MarketCommunity, self).__init__(dispersy, master, my_member)
        self.logger = logging.getLogger('MarketLogger')
        self.data_manager = None
        self.rest_manager = None
        self.market_api = None

    def initialize(self, role, rest_api_port):
        super(MarketCommunity, self).initialize()

        self.data_manager = MarketDataManager(User(self.my_member.public_key.encode('hex'), role=Role(role)))
        self.rest_manager = RESTManager(self, rest_api_port)
        self.market_api = self.rest_manager.start()

        self.logger.info("MarketCommunity initialized")

    @classmethod
    def get_master_members(cls, dispersy):
        # generated: Fri Feb 24 11:22:22 2017
        # curve: None
        # len: 571 bits ~ 144 bytes signature
        # pub: 170 3081a7301006072a8648ce3d020106052b81040027038192000407bacf5ae4d3fe94d49a7f94b7239e9c2d878b29f0fbdb7374d5b6a09d9d6fba80d3807affd0ba45ba1ac1c278ca59bec422d8a44b5fefaabcdd62c2778414c01da4578b304b104b00eec74de98dcda803b79fd1783d76cc1bd7aab75cfd8fff9827a9647ae3c59423c2a9a984700e7cb43b881a6455574032cc11dba806dba9699f54f2d30b10eed5c7c0381a0915a5
        # pub-sha1 56553661e30b342b2fc39f1a425eb612ef8b8c33
        # -----BEGIN PUBLIC KEY-----
        # MIGnMBAGByqGSM49AgEGBSuBBAAnA4GSAAQHus9a5NP+lNSaf5S3I56cLYeLKfD7
        # 23N01bagnZ1vuoDTgHr/0LpFuhrBwnjKWb7EItikS1/vqrzdYsJ3hBTAHaRXizBL
        # EEsA7sdN6Y3NqAO3n9F4PXbMG9eqt1z9j/+YJ6lkeuPFlCPCqamEcA58tDuIGmRV
        # V0AyzBHbqAbbqWmfVPLTCxDu1cfAOBoJFaU=
        # -----END PUBLIC KEY-----
        master_key = "3081a7301006072a8648ce3d020106052b81040027038192000407bacf5ae4d3fe94d49a7f94b7239e9c2d878b29" + \
                     "f0fbdb7374d5b6a09d9d6fba80d3807affd0ba45ba1ac1c278ca59bec422d8a44b5fefaabcdd62c2778414c01da4" + \
                     "578b304b104b00eec74de98dcda803b79fd1783d76cc1bd7aab75cfd8fff9827a9647ae3c59423c2a9a984700e7c" + \
                     "b43b881a6455574032cc11dba806dba9699f54f2d30b10eed5c7c0381a0915a5"
        master = dispersy.get_member(public_key=master_key.decode("HEX"))
        return [master]

    def initiate_meta_messages(self):
        meta_messages = super(MarketCommunity, self).initiate_meta_messages()

        return meta_messages + [Message(self, u"user-request",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_user_request),
                                Message(self, u"user-response",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_user_response),
                                Message(self, u"loan-request",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_loan_request),
                                Message(self, u"loan-reject",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_loan_reject),
                                Message(self, u"mortgage-offer",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_mortgage_offer),
                                Message(self, u"mortgage-accept",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_mortgage_accept),
                                Message(self, u"mortgage-reject",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_mortgage_reject),
                                Message(self, u"investment-offer",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_investment_offer),
                                Message(self, u"investment-accept",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_investment_accept),
                                Message(self, u"investment-reject",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_investment_reject),
                                Message(self, u"campaign-update",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        FullSyncDistribution(enable_sequence_number=False,
                                                             synchronization_direction=u"DESC",
                                                             priority=128),
                                        CommunityDestination(node_count=10),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_campaign_update)]

    def initiate_conversions(self):
        return [DefaultConversion(self), MarketConversion(self)]

    @inlineCallbacks
    def unload_community(self):
        yield self.rest_manager.stop()
        yield super(MarketCommunity, self).unload_community()

    def on_introduction_response(self, messages):
        super(MarketCommunity, self).on_introduction_response(messages)
        for message in messages:
            self.send_user_request(message.candidate)

    def send_message_to_ids(self, msg_type, user_ids, payload_dict):
        candidates = []
        for user_id in user_ids:
            user = self.data_manager.get_user(user_id)
            candidate = user.candidate if user else None
            if candidate is None:
                self.logger.error('Cannot send %s (unknown user)', msg_type)
                return False
            candidates.append(candidate)
        return self.send_message(msg_type, tuple(candidates), payload_dict)

    def send_message(self, msg_type, candidates, payload_dict):
        self.logger.debug('Sending %s message to %d candidate(s)', msg_type, len(candidates))
        meta = self.get_meta_message(msg_type)
        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            destination=candidates,
                            payload=(payload_dict,))
        return self.dispersy.store_update_forward([message], False, False, True)

    @property
    def my_role(self):
        return self.data_manager.you.role

    @property
    def my_user(self):
        return self.data_manager.you

    @property
    def my_user_dict(self):
        you = self.data_manager.you
        profile = you.profile

        usr = you.to_dict()

        if profile is not None:
            usr.update({'profile': {'first_name': profile.first_name,
                                    'last_name': profile.last_name,
                                    'email': profile.email,
                                    'iban': profile.iban,
                                    'phone_number': profile.phone_number}})
        return usr

    def add_or_update_user(self, candidate, role=Role.UNKNOWN):
        user_id = candidate.get_member().public_key.encode('hex')
        user = self.data_manager.get_user(user_id)
        if user is not None:
            user.role = role
        else:
            user = self.data_manager.users[user_id] = User(user_id, role=role)
        user.candidate = candidate
        return user

    def add_or_update_profile(self, candidate, profile):
        user_id = candidate.get_member().public_key.encode('hex')
        user = self.data_manager.get_user(user_id)
        if user is not None and profile is not None:
            if isinstance(user.profile, InvestorProfile) or \
               isinstance(profile, BorrowersProfile) or user.profile is None:
                user.profile = profile
            else:
                # Don't overwrite the complete profile (in case of BorrowerProfile)
                user.profile.first_name = profile.first_name
                user.profile.last_name = profile.last_name
                user.profile.email = profile.email
                user.profile.iban = profile.iban
                user.profile.phone_number = profile.phone_number

    def send_user_request(self, candidate):
        self.send_message(u'user-request', (candidate,), {'user': self.my_user_dict})

    def send_user_response(self, candidate):
        self.send_message(u'user-response', (candidate,), {'user': self.my_user_dict})

    def _process_user(self, candidate, user_dict):
        user = User.from_dict(user_dict)
        self.add_or_update_user(candidate, role=user.role)

        if 'profile' in user_dict:
            profile = InvestorProfile.from_dict(user_dict['profile'])
            self.add_or_update_profile(candidate, profile)

    def on_user_request(self, messages):
        for message in messages:
            self._process_user(message.candidate, message.payload.dictionary['user'])
            self.logger.debug('Got user-request from %s (role=%s)',
                              message.candidate.sock_addr,
                              message.payload.dictionary['user']['role'])
            self.send_user_response(message.candidate)

    def on_user_response(self, messages):
        for message in messages:
            self._process_user(message.candidate, message.payload.dictionary['user'])
            self.logger.debug('Got user-response from %s (role=%s)',
                              message.candidate.sock_addr,
                              message.payload.dictionary['user']['role'])

    def send_loan_request(self, loan_request):
        msg_dict = {'loan_request': loan_request.to_dict(),
                    'borrowers_profile': self.data_manager.you.profile.to_dict()}

        return self.send_message_to_ids(u'loan-request', loan_request.bank_ids, msg_dict)

    def on_loan_request(self, messages):
        for message in messages:
            if self.my_role != Role.FINANCIAL_INSTITUTION:
                self.logger.warning('Dropping loan-request from %s (not a financial institution)',
                                    message.candidate.sock_addr)
                continue

            self.logger.debug('Got loan-request from %s', message.candidate.sock_addr)

            loan_request_dict = message.payload.dictionary['loan_request']
            loan_request = LoanRequest.from_dict(loan_request_dict)

            if loan_request is None:
                self.logger.warning('Dropping invalid loan-request from %s', message.candidate.sock_addr)
                continue

            borrowers_profile_dict = message.payload.dictionary['borrowers_profile']
            borrowers_profile = BorrowersProfile.from_dict(borrowers_profile_dict)

            # We're deliberately not using loan_request.user_id
            user = self.add_or_update_user(message.candidate, role=Role.BORROWER)
            self.add_or_update_profile(message.candidate, borrowers_profile)

            user.loan_requests.append(loan_request)

    def send_loan_reject(self, loan_request):
        return self.send_message_to_ids(u'loan-reject', (loan_request.user_id,), {'loan_request_id': loan_request.id})

    def on_loan_reject(self, messages):
        for message in messages:
            loan_request = self.data_manager.get_loan_request(message.payload.dictionary['loan_request_id'])

            if loan_request:
                self.logger.debug('Got loan-reject from %s', message.candidate.sock_addr)
                loan_request.status = LoanRequestStatus.REJECTED
            else:
                self.logger.warning('Dropping loan-reject from %s (unknown loan request)', message.candidate.sock_addr)

    def send_mortgage_offer(self, loan_request, mortgage):
        return self.send_message_to_ids(u'mortgage-offer', (loan_request.user_id,),
                                        {'loan_request_id': loan_request.id,
                                         'mortgage': mortgage.to_dict()})

    def on_mortgage_offer(self, message):
        for message in message:
            loan_request = self.data_manager.get_loan_request(message.payload.dictionary['loan_request_id'])

            if not loan_request:
                self.logger.warning('Dropping mortgage-offer from %s (unknown loan request)', message.candidate.sock_addr)
                continue

            self.logger.debug('Got mortgage-offer from %s', message.candidate.sock_addr)

            mortgage_dict = message.payload.dictionary['mortgage']
            mortgage = Mortgage.from_dict(mortgage_dict)

            if mortgage is None:
                self.logger.warning('Dropping invalid mortgage-offer from %s', message.candidate.sock_addr)
                continue

            self.add_or_update_user(message.candidate, role=Role.FINANCIAL_INSTITUTION)

            # TODO: check if sender == mortgage.bank_id

            loan_request.status = LoanRequestStatus.ACCEPTED
            loan_request.mortgage = mortgage
            self.data_manager.you.mortgages.append(mortgage)

    def send_mortgage_accept(self, mortgage):
        if self.send_message_to_ids(u'mortgage-accept', (mortgage.bank_id,), {'mortgage_id': mortgage.id}):
            # Campaign ends in 30 days
            end_time = int(time.time()) + 30 * 24 * 60 * 60
            finance_goal = mortgage.amount - mortgage.bank_amount
            campaign = Campaign(self.my_user.id, mortgage, finance_goal, end_time, False)
            self.data_manager.you.campaigns.append(campaign)
            return self.send_campaign_update(campaign)
        return False

    def on_mortgage_accept(self, messages):
        for message in messages:
            mortgage = self.data_manager.get_mortgage(message.payload.dictionary['mortgage_id'])

            if not mortgage:
                self.logger.warning('Dropping mortgage-accept from %s (unknown mortgage)', message.candidate.sock_addr)
                continue

            self.logger.debug('Got mortgage-accept from %s', message.candidate.sock_addr)

            mortgage.status = MortgageStatus.ACCEPTED

    def send_mortgage_reject(self, mortgage):
        return self.send_message_to_ids(u'mortgage-reject', (mortgage.bank_id,), {'mortgage_id': mortgage.id})

    def on_mortgage_reject(self, messages):
        for message in messages:
            mortgage = self.data_manager.get_mortgage(message.payload.dictionary['mortgage_id'])

            if mortgage:
                self.logger.debug('Got mortgage-reject from %s', message.candidate.sock_addr)
                mortgage.status = MortgageStatus.REJECTED
            else:
                self.logger.warning('Dropping mortgage-reject from %s (unknown mortgage)', message.candidate.sock_addr)

    def send_investment_offer(self, investment):
        mortgage = self.data_manager.get_mortgage(investment.mortgage_id)
        if not mortgage:
            self.logger.error('Cannot send investment-offer (unknown mortgage)')
            return False

        return self.send_message_to_ids(u'investment-offer', (mortgage.user_id,),
                                        {'investment': investment.to_dict(),
                                         'investor_profile': self.data_manager.you.profile.to_dict()})

    def on_investment_offer(self, messages):
        for message in messages:
            investment_dict = message.payload.dictionary['investment']
            investment = Investment.from_dict(investment_dict)

            mortgage = self.data_manager.get_mortgage(investment.mortgage_id)

            if mortgage is None:
                self.logger.warning('Dropping investment-offer from %s (unknown mortgage)', message.candidate.sock_addr)
                continue

            profile_dict = message.payload.dictionary['investor_profile']
            profile = InvestorProfile.from_dict(profile_dict)
            self.add_or_update_profile(message.candidate, profile)

            mortgage.investments.append(investment)

            self.logger.debug('Got investment-offer from %s', message.candidate.sock_addr)

    def send_investment_accept(self, investment):
        return self.send_message_to_ids(u'investment-accept', (investment.user_id,),
                                        {'investment_id': investment.id,
                                         'borrowers_profile': self.data_manager.you.profile.to_dict()})

    def on_investment_accept(self, messages):
        for message in messages:
            investment = self.data_manager.get_investment(message.payload.dictionary['investment_id'])

            if investment is None:
                self.logger.warning('Dropping investment-accept from %s (unknown investment)', message.candidate.sock_addr)
                continue

            profile_dict = message.payload.dictionary['borrowers_profile']
            profile = BorrowersProfile.from_dict(profile_dict)
            self.add_or_update_profile(message.candidate, profile)

            investment.status = InvestmentStatus.ACCEPTED

            self.logger.debug('Got investment-accept from %s', message.candidate.sock_addr)

    def send_investment_reject(self, investment):
        return self.send_message_to_ids(u'investment-reject', (investment.user_id,), {'investment_id': investment.id})

    def on_investment_reject(self, messages):
        for message in messages:
            investment = self.data_manager.get_investment(message.payload.dictionary['investment_id'])

            if investment is None:
                self.logger.warning('Dropping investment-reject from %s (unknown investment)', message.candidate.sock_addr)
                continue

            self.logger.debug('Got investment-reject from %s', message.candidate.sock_addr)
            investment.status = MortgageStatus.REJECTED

    def send_campaign_update(self, campaign, investment=None):
        msg_dict = {'campaign': campaign.to_dict()}
        if investment is not None:
            msg_dict['investment'] = investment.to_dict()

        meta = self.get_meta_message(u'campaign-update')
        message = meta.impl(authentication=(self._my_member,),
                            distribution=(self.claim_global_time(),),
                            payload=(msg_dict,))
        return self._dispersy.store_update_forward([message], True, True, True)

    def on_campaign_update(self, messages):
        for message in messages:
            campaign_dict = message.payload.dictionary['campaign']
            campaign = Campaign.from_dict(campaign_dict)

            investment = Investment.from_dict(message.payload.dictionary['investment']) \
                         if 'investment' in message.payload.dictionary else None

            if campaign is None:
                self.logger.warning('Dropping invalid campaign-update from %s', message.candidate.sock_addr)
                continue

            # TODO: check for user in check method?
            user = self.data_manager.get_user(campaign.user_id)
            if user is None:
                self.logger.warning('Dropping campaign-update (unknown user_id)')
                continue

            self.logger.debug('Got campaign-update')

            mortgage = campaign.mortgage
            user = self.data_manager.get_user(mortgage.user_id)
            if user is None:
                user = self.data_manager.users[mortgage.user_id] = User(mortgage.user_id, role=Role.BORROWER)
            # TODO: check if this message is signed by the mortgage owner

            if self.data_manager.get_mortgage(campaign.mortgage.id) is None:
                user.mortgages.append(mortgage)

            if self.data_manager.get_campaign(campaign.mortgage.id) is None:
                self.data_manager.campaigns[campaign.mortgage.id] = campaign

            if investment:
                mortgage.investments.append(investment)

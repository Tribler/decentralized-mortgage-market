import os
import time
import hashlib
import logging

from base64 import b64encode
from collections import OrderedDict
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall

from market.community import accept
from market.community.conversion import MarketConversion
from market.community.payload import ProtobufPayload
from market.database.datamanager import MarketDataManager
from market.dispersy.authentication import MemberAuthentication
from market.dispersy.candidate import Candidate
from market.dispersy.community import Community
from market.dispersy.conversion import DefaultConversion
from market.dispersy.destination import CommunityDestination, CandidateDestination
from market.dispersy.distribution import DirectDistribution, FullSyncDistribution
from market.dispersy.message import Message
from market.dispersy.resolution import PublicResolution
from market.dispersy.requestcache import RandomNumberCache
from market.models.loanrequest import LoanRequest, LoanRequestStatus
from market.models.mortgage import Mortgage, MortgageStatus
from market.models.user import User, Role
from market.models.campaign import Campaign
from market.models.investment import InvestmentStatus, Investment
from market.models import investment
from market.models.profile import Profile
from market.models.block import Block
from market.models.contract import Contract, ContractType
from market.restapi.rest_manager import RESTManager
from market.util.uint256 import bytes_to_uint256
from market.util.math import median

COMMIT_INTERVAL = 60
CLEANUP_INTERVAL = 60

BLOCK_CREATION_INTERNAL = 1
BLOCK_TARGET_SPACING = 10 * 60
BLOCK_TARGET_TIMESPAN = 20 * 60  # 14 * 24 * 60 * 60
BLOCK_TARGET_BLOCKSPAN = BLOCK_TARGET_TIMESPAN / BLOCK_TARGET_SPACING
BLOCK_DIFFICULTY_INIT = 0x00ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
BLOCK_DIFFICULTY_MIN = 0x00ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
BLOCK_GENESIS_HASH = '\00' * 32

MAX_CLOCK_DRIFT = 15 * 60
MAX_PACKET_SIZE = 1500
DEFAULT_CAMPAIGN_DURATION = 30 * 24 * 60 * 60


class SignatureRequestCache(RandomNumberCache):

    def __init__(self, community):
        super(SignatureRequestCache, self).__init__(community.request_cache, u'signature-request')
        self.community = community

    def on_timeout(self):
        pass


class BlockRequestCache(RandomNumberCache):

    def __init__(self, community, block_id):
        super(BlockRequestCache, self).__init__(community.request_cache, u'block-request')
        self.community = community
        self.block_id = block_id

    def on_timeout(self):
        # Retry to download block
        self.community.send_block_request(self.block_id)


class MarketCommunity(Community):

    def __init__(self, dispersy, master, my_member):
        super(MarketCommunity, self).__init__(dispersy, master, my_member)
        self.logger = logging.getLogger('MarketLogger')
        self.id_to_candidate = {}
        self.incoming_contracts = OrderedDict()
        self.incoming_blocks = {}
        self.data_manager = None
        self.rest_manager = None
        self.market_api = None

    def initialize(self, role, rest_api_port):
        super(MarketCommunity, self).initialize()

        market_db = os.path.join(self.dispersy.working_directory, 'market.db')
        self.data_manager = MarketDataManager(market_db)
        self.data_manager.load_my_user(self.my_user_id, Role(role))

        self.rest_manager = RESTManager(self, rest_api_port)
        self.market_api = self.rest_manager.start()

        self.register_task('commit', LoopingCall(self.data_manager.commit)).start(COMMIT_INTERVAL)
        self.register_task('cleanup', LoopingCall(self.cleanup)).start(CLEANUP_INTERVAL)
        if self.my_user.role == Role.FINANCIAL_INSTITUTION:
            self.register_task('create_block', LoopingCall(self.create_block)).start(BLOCK_CREATION_INTERNAL)

        self.logger.info('MarketCommunity initialized')

    @classmethod
    def get_master_members(cls, dispersy):
        # generated: Fri Feb 24 11:22:22 2017
        # curve: None
        # len: 571 bits ~ 144 bytes signature
        # pub: 170 3081a7301006072a8648ce3d020106052b81040027038192000407b
        # acf5ae4d3fe94d49a7f94b7239e9c2d878b29f0fbdb7374d5b6a09d9d6fba80d
        # 3807affd0ba45ba1ac1c278ca59bec422d8a44b5fefaabcdd62c2778414c01da
        # 4578b304b104b00eec74de98dcda803b79fd1783d76cc1bd7aab75cfd8fff982
        # 7a9647ae3c59423c2a9a984700e7cb43b881a6455574032cc11dba806dba9699
        # f54f2d30b10eed5c7c0381a0915a5
        # pub-sha1 56553661e30b342b2fc39f1a425eb612ef8b8c33
        # -----BEGIN PUBLIC KEY-----
        # MIGnMBAGByqGSM49AgEGBSuBBAAnA4GSAAQHus9a5NP+lNSaf5S3I56cLYeLKfD7
        # 23N01bagnZ1vuoDTgHr/0LpFuhrBwnjKWb7EItikS1/vqrzdYsJ3hBTAHaRXizBL
        # EEsA7sdN6Y3NqAO3n9F4PXbMG9eqt1z9j/+YJ6lkeuPFlCPCqamEcA58tDuIGmRV
        # V0AyzBHbqAbbqWmfVPLTCxDu1cfAOBoJFaU=
        # -----END PUBLIC KEY-----
        master_key = '3081a7301006072a8648ce3d020106052b81040027038192000407bacf5ae4d3fe94d49a7f94b7239e9c2d878b29' + \
                     'f0fbdb7374d5b6a09d9d6fba80d3807affd0ba45ba1ac1c278ca59bec422d8a44b5fefaabcdd62c2778414c01da4' + \
                     '578b304b104b00eec74de98dcda803b79fd1783d76cc1bd7aab75cfd8fff9827a9647ae3c59423c2a9a984700e7c' + \
                     'b43b881a6455574032cc11dba806dba9699f54f2d30b10eed5c7c0381a0915a5'
        master = dispersy.get_member(public_key=master_key.decode('hex'))
        return [master]

    def initiate_meta_messages(self):
        meta_messages = super(MarketCommunity, self).initiate_meta_messages()

        return meta_messages + [
            # Messages for gossiping user information
            Message(self, u"user-request",
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
            # Mortgage agreement messages
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
            # Investment agreement messages
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
                    self.on_campaign_update),
            # Blockchain related messages
            Message(self, u"signature-request",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_signature_request),
            Message(self, u"signature-response",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_signature_response),
            Message(self, u"contract",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_contract),
            Message(self, u"block-request",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_block_request),
            Message(self, u"block",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_block)
        ]

    def initiate_conversions(self):
        return [DefaultConversion(self), MarketConversion(self)]

    @inlineCallbacks
    def unload_community(self):
        yield self.rest_manager.stop()
        yield super(MarketCommunity, self).unload_community()

    def cleanup(self):
        for user_id, candidate in self.id_to_candidate.items():
            if candidate.last_walk_reply < time.time() - 300:
                self.id_to_candidate.pop(user_id)

    def on_introduction_response(self, messages):
        super(MarketCommunity, self).on_introduction_response(messages)
        for message in messages:
            self.send_user_request(message.candidate)

    def send_message_to_ids(self, msg_type, user_ids, payload_dict):
        candidates = []
        for user_id in user_ids:
            candidate = self.id_to_candidate.get(user_id)
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

    def multicast_message(self, msg_type, payload_dict, role=None, exclude=None):
        candidates = [self.id_to_candidate[user.id] for user in self.data_manager.get_users()
                      if user.id in self.id_to_candidate and (role is None or user.role == role)]

        if exclude in candidates:
            candidates.remove(exclude)

        return self.send_message(msg_type, tuple(candidates), payload_dict)

    @property
    def my_role(self):
        return self.my_user.role

    @property
    def my_user(self):
        return self.data_manager.get_user(self.my_user_id)

    @property
    def my_user_id(self):
        return self.my_member.public_key

    @property
    def my_user_dict(self):
        user_dict = self.my_user.to_dict()

        profile = self.my_user.profile
        if profile is not None:
            user_dict.update({'profile': {'first_name': profile.first_name,
                                          'last_name': profile.last_name,
                                          'email': profile.email,
                                          'iban': profile.iban,
                                          'phone_number': profile.phone_number}})
        return user_dict

    def add_or_update_user(self, candidate, role=Role.UNKNOWN):
        user_id = candidate.get_member().public_key
        user = self.data_manager.get_user(user_id)
        if user is not None:
            user.role = role
        else:
            user = User(user_id, role=role)
            self.data_manager.add_user(user)
        self.id_to_candidate[user_id] = candidate
        return user

    def add_or_update_profile(self, candidate, profile):
        user_id = candidate.get_member().public_key
        user = self.data_manager.get_user(user_id)
        if profile is not None:
            if user.profile is None:
                user.profile = profile
            else:
                user.profile.merge(profile)

    def send_user_request(self, candidate):
        self.send_message(u'user-request', (candidate,), {'user': self.my_user_dict})

    def send_user_response(self, candidate):
        self.send_message(u'user-response', (candidate,), {'user': self.my_user_dict})

    def _process_user(self, candidate, user_dict):
        user = User.from_dict(user_dict)
        self.add_or_update_user(candidate, role=user.role)

        if 'profile' in user_dict:
            profile = Profile.from_dict(user_dict['profile'])
            self.add_or_update_profile(candidate, profile)
        return user

    def on_user_request(self, messages):
        for message in messages:
            user = self._process_user(message.candidate, message.payload.dictionary['user'])
            self.logger.debug('Got user-request from %s (role=%s)',
                              message.candidate.sock_addr,
                              user.role)
            self.send_user_response(message.candidate)

    def on_user_response(self, messages):
        for message in messages:
            user = self._process_user(message.candidate, message.payload.dictionary['user'])
            self.logger.debug('Got user-response from %s (role=%s)',
                              message.candidate.sock_addr,
                              user.role)

    def send_loan_request(self, loan_request):
        msg_dict = {'loan_request': loan_request.to_dict(),
                    'borrowers_profile': self.data_manager.you.profile.to_dict()}

        return self.send_message_to_ids(u'loan-request', (loan_request.bank_id,), msg_dict)

    @accept(local=Role.FINANCIAL_INSTITUTION, remote=Role.BORROWER)
    def on_loan_request(self, messages):
        for message in messages:
            self.logger.debug('Got loan-request from %s', message.candidate.sock_addr)

            loan_request_dict = message.payload.dictionary['loan_request']
            loan_request = LoanRequest.from_dict(loan_request_dict)

            if loan_request is None:
                self.logger.warning('Dropping invalid loan-request from %s', message.candidate.sock_addr)
                continue

            borrowers_profile_dict = message.payload.dictionary['borrowers_profile']
            borrowers_profile = Profile.from_dict(borrowers_profile_dict)

            # We're deliberately not using loan_request.user_id
            user = self.add_or_update_user(message.candidate, role=Role.BORROWER)
            self.add_or_update_profile(message.candidate, borrowers_profile)

            user.loan_requests.add(loan_request)

    def send_loan_reject(self, loan_request):
        return self.send_message_to_ids(u'loan-reject', (loan_request.user_id,), {'loan_request_id': loan_request.id,
                                                                                  'loan_request_user_id': loan_request.user_id})

    @accept(local=Role.BORROWER, remote=Role.FINANCIAL_INSTITUTION)
    def on_loan_reject(self, messages):
        for message in messages:
            loan_request = self.data_manager.get_loan_request(message.payload.dictionary['loan_request_id'],
                                                              message.payload.dictionary['loan_request_user_id'])

            if loan_request:
                self.logger.debug('Got loan-reject from %s', message.candidate.sock_addr)
                loan_request.status = LoanRequestStatus.REJECTED
            else:
                self.logger.warning('Dropping loan-reject from %s (unknown loan request)', message.candidate.sock_addr)

    def send_mortgage_offer(self, loan_request, mortgage):
        return self.send_message_to_ids(u'mortgage-offer', (mortgage.user_id,),
                                        {'loan_request_id': loan_request.id,
                                         'loan_request_user_id': loan_request.user_id,
                                         'mortgage': mortgage.to_dict()})

    @accept(local=Role.BORROWER, remote=Role.FINANCIAL_INSTITUTION)
    def on_mortgage_offer(self, message):
        for message in message:
            loan_request = self.data_manager.get_loan_request(message.payload.dictionary['loan_request_id'],
                                                              message.payload.dictionary['loan_request_user_id'])

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
            self.data_manager.you.mortgages.add(mortgage)

    def send_mortgage_accept(self, mortgage):
        return self.send_message_to_ids(u'mortgage-accept', (mortgage.bank_id,), {'mortgage_id': mortgage.id,
                                                                                  'mortgage_user_id': mortgage.user_id})

    @accept(local=Role.FINANCIAL_INSTITUTION, remote=Role.BORROWER)
    def on_mortgage_accept(self, messages):
        for message in messages:
            mortgage = self.data_manager.get_mortgage(message.payload.dictionary['mortgage_id'],
                                                      message.payload.dictionary['mortgage_user_id'])

            if mortgage is None:
                self.logger.warning('Dropping mortgage-accept from %s (unknown mortgage)', message.candidate.sock_addr)
                continue

            self.logger.debug('Got mortgage-accept from %s', message.candidate.sock_addr)

            # Set status before creating the contract
            mortgage.status = MortgageStatus.ACCEPTED

            self.send_contract(mortgage.to_bin(), ContractType.MORTGAGE, self.my_user_id, mortgage.user_id)

            end_time = int(time.time()) + DEFAULT_CAMPAIGN_DURATION
            finance_goal = mortgage.amount - mortgage.bank_amount
            campaign = Campaign(self.data_manager.you.campaigns.count(), self.my_user_id, mortgage.id, mortgage.user_id, finance_goal, end_time, False)
            self.data_manager.you.campaigns.add(campaign)

    def send_mortgage_reject(self, mortgage):
        return self.send_message_to_ids(u'mortgage-reject', (mortgage.bank_id,), {'mortgage_id': mortgage.id,
                                                                                  'mortgage_user_id': mortgage.user_id})

    @accept(local=Role.FINANCIAL_INSTITUTION, remote=Role.BORROWER)
    def on_mortgage_reject(self, messages):
        for message in messages:
            mortgage = self.data_manager.get_mortgage(message.payload.dictionary['mortgage_id'],
                                                      message.payload.dictionary['mortgage_user_id'])

            if mortgage:
                self.logger.debug('Got mortgage-reject from %s', message.candidate.sock_addr)
                mortgage.status = MortgageStatus.REJECTED
            else:
                self.logger.warning('Dropping mortgage-reject from %s (unknown mortgage)', message.candidate.sock_addr)

    def send_investment_offer(self, investment):
        campaign = self.data_manager.get_campaign(investment.campaign_id, investment.campaign_user_id)
        if campaign is None:
            self.logger.error('Cannot send investment-offer (unknown campaign)')
            return False

        return self.send_message_to_ids(u'investment-offer', (campaign.user_id,),
                                        {'investment': investment.to_dict(),
                                         'investor_profile': self.data_manager.you.profile.to_dict()})

    @accept(local=Role.FINANCIAL_INSTITUTION, remote=Role.INVESTOR)
    def on_investment_offer(self, messages):
        for message in messages:
            investment_dict = message.payload.dictionary['investment']
            investment = Investment.from_dict(investment_dict)

            campaign = self.data_manager.get_campaign(investment.campaign_id, investment.campaign_user_id)

            if campaign is None:
                self.logger.warning('Dropping investment-offer from %s (unknown campaign)', message.candidate.sock_addr)
                continue

            # TODO: auto reject if we are offered more money than we need

            profile_dict = message.payload.dictionary['investor_profile']
            profile = Profile.from_dict(profile_dict)
            self.add_or_update_profile(message.candidate, profile)

            campaign.investments.add(investment)

            self.logger.debug('Got investment-offer from %s', message.candidate.sock_addr)

    def send_investment_accept(self, investment):
        # TODO: send along a bank profile?
        return self.send_message_to_ids(u'investment-accept', (investment.user_id,),
                                        {'investment_id': investment.id,
                                         'investment_user_id': investment.user_id})

    @accept(local=Role.INVESTOR, remote=Role.FINANCIAL_INSTITUTION)
    def on_investment_accept(self, messages):
        for message in messages:
            investment = self.data_manager.get_investment(message.payload.dictionary['investment_id'],
                                                          message.payload.dictionary['investment_user_id'])

            if investment is None:
                self.logger.warning('Dropping investment-accept from %s (unknown investment)', message.candidate.sock_addr)
                continue

            self.logger.debug('Got investment-accept from %s', message.candidate.sock_addr)

            # Set status before creating the contract
            investment.status = InvestmentStatus.ACCEPTED

            self.send_contract(investment.to_bin(), ContractType.INVESTMENT, self.my_user_id, investment.campaign_user_id)

    def send_investment_reject(self, investment):
        return self.send_message_to_ids(u'investment-reject', (investment.user_id,), {'investment_id': investment.id,
                                                                                      'investment_user_id': investment.user_id})

    @accept(local=Role.INVESTOR, remote=Role.FINANCIAL_INSTITUTION)
    def on_investment_reject(self, messages):
        for message in messages:
            investment = self.data_manager.get_investment(message.payload.dictionary['investment_id'],
                                                          message.payload.dictionary['investment_user_id'])

            if investment is None:
                self.logger.warning('Dropping investment-reject from %s (unknown investment)', message.candidate.sock_addr)
                continue

            self.logger.debug('Got investment-reject from %s', message.candidate.sock_addr)
            investment.status = InvestmentStatus.REJECTED

    def send_campaign_update(self, campaign, investment=None):
        mortgage = self.data_manager.get_mortgage(campaign.mortgage_id, campaign.mortgage_user_id)
        msg_dict = {'campaign': campaign.to_dict(),
                    'mortgage': mortgage.to_dict()}
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

            mortgage_dict = message.payload.dictionary['mortgage']
            mortgage = Mortgage.from_dict(mortgage_dict)

            investment = Investment.from_dict(message.payload.dictionary['investment']) \
                         if 'investment' in message.payload.dictionary else None

            if campaign is None or mortgage is None:
                self.logger.warning('Dropping invalid campaign-update from %s', message.candidate.sock_addr)
                continue

            # TODO: check for user in check method?
            bank = self.data_manager.get_user(campaign.user_id)
            if bank is None:
                self.logger.warning('Dropping campaign-update (unknown user_id)')
                continue

            self.logger.debug('Got campaign-update')

            user = self.data_manager.get_user(mortgage.user_id)
            if user is None:
                user = User(mortgage.user_id, role=Role.BORROWER)
                self.data_manager.add_user(user)
            # TODO: check if this message is signed by the mortgage owner

            if self.data_manager.get_mortgage(mortgage.id, mortgage.user_id) is None:
                user.mortgages.add(mortgage)

            existing_campaign = self.data_manager.get_campaign(campaign.id, campaign.user_id)
            if existing_campaign is None:
                bank.campaigns.add(campaign)
            else:
                campaign = existing_campaign

            if investment and self.data_manager.get_investment(investment.id, investment.user_id) is None:
                campaign.investments.add(investment)

    def send_signature_request(self, contract):
        cache = self.request_cache.add(SignatureRequestCache(self))

        destionation_id = contract.to_id if contract.from_id == self.my_user_id else contract.from_id

        return self.send_message_to_ids(u'signature-request', (destionation_id,), {'identifier': cache.number,
                                                                                   'contract': contract.to_dict()})

    def on_signature_request(self, messages):
        for message in messages:
            contract = Contract.from_dict(message.payload.dictionary['contract'])
            if contract is None:
                self.logger.warning('Dropping invalid signature-request from %s', message.candidate.sock_addr)
                continue
            elif not contract.verify(message.candidate.get_member()):
                self.logger.warning('Dropping signature-request with incorrect signature')
                continue

            self.logger.debug('Got signature-request from %s', message.candidate.sock_addr)

            if contract.contract_type == ContractType.INVESTMENT:
                # Find & set previous_hash
                investment = contract.get_object()
                campaign = self.data_manager.get_campaign(investment.campaign_id, investment.campaign_user_id)
                if campaign is None:
                    self.warning('Could not find campaign')
                    continue
                mortgage = self.data_manager.get_mortgage(campaign.mortgage_id, campaign.mortgage_user_id)
                if mortgage is None:
                    self.warning('Could not find mortgage')
                    continue
                contract.previous_hash = mortgage.contract_id

            if self.process_contract(contract, sign=True):
                self.send_signature_response(message.candidate, contract, message.payload.dictionary['identifier'])
                self.incoming_contracts[contract.id] = contract
                self.multicast_message(u'contract', {'contract': contract.to_dict()}, role=Role.FINANCIAL_INSTITUTION)

    def send_signature_response(self, candidate, contract, identifier):
        return self.send_message(u'signature-response', (candidate,), {'identifier': identifier,
                                                                       'contract': contract.to_dict()})

    def on_signature_response(self, messages):
        for message in messages:
            cache = self.request_cache.get(u'signature-request', message.payload.dictionary['identifier'])
            if not cache:
                self.logger.warning("Dropping unexpected signature-response from %s", message.candidate.sock_addr)
                continue

            contract = Contract.from_dict(message.payload.dictionary['contract'])
            if contract is None:
                self.logger.warning('Dropping invalid signature-response from %s', message.candidate.sock_addr)
                continue
            elif not contract.verify(message.candidate.get_member()):
                self.logger.warning('Dropping signature-response with incorrect signature')
                continue

            self.logger.debug('Got signature-response from %s', message.candidate.sock_addr)

            if self.process_contract(contract):
                self.incoming_contracts[contract.id] = contract
                self.multicast_message(u'contract', {'contract': contract.to_dict()}, role=Role.FINANCIAL_INSTITUTION)

    @accept(local=Role.FINANCIAL_INSTITUTION)
    def on_contract(self, messages):
        for message in messages:
            contract = Contract.from_dict(message.payload.dictionary['contract'])
            self.logger.debug('Got contract with id %s', b64encode(contract.id))

            # Forward if needed
            if contract.id not in self.incoming_contracts:
                self.incoming_contracts[contract.id] = contract
                self.multicast_message(u'contract', {'contract': contract.to_dict()},
                                       role=Role.FINANCIAL_INSTITUTION, exclude=message.candidate)

    def send_block_request(self, block_id):
        self.request_cache.add(BlockRequestCache(self, block_id))
        candidate = next((self.id_to_candidate[user.id] for user in self.data_manager.get_users() \
                          if user.id in self.id_to_candidate and user.role == Role.FINANCIAL_INSTITUTION), None)
        self.send_message(u'block-request', (candidate,), {'block_id': block_id})

    @accept(local=Role.FINANCIAL_INSTITUTION, remote=Role.FINANCIAL_INSTITUTION)
    def on_block_request(self, messages):
        for message in messages:
            block_id = message.payload.dictionary['block_id']
            self.logger.debug('Got block-request for id %s', b64encode(block_id))

            block = self.data_manager.get_block(block_id)
            if block is not None:
                self.send_message(u'block', (message.candidate,), {'block': block.to_dict()})

    @accept(local=Role.FINANCIAL_INSTITUTION, remote=Role.FINANCIAL_INSTITUTION)
    def on_block(self, messages):
        for message in messages:
            block = Block.from_dict(message.payload.dictionary['block'])
            if not block:
                self.logger.warning('Dropping invalid block from %s', message.candidate.sock_addr)
                continue
            elif not self.check_block(block):
                self.logger.warning('Dropping illegal block from %s', message.candidate.sock_addr)
                continue

            self.logger.debug('Got block with id %s', b64encode(block.id))

            # If we're trying to download this block, stop it
            # TODO: fix this
            for cache in self.request_cache._identifiers.values():
                if isinstance(cache, BlockRequestCache) and cache.block_id == block.id:
                    self.request_cache.pop(cache.prefix, cache.number)

            # Are we dealing with an orphan block?
            if block.previous_hash != BLOCK_GENESIS_HASH and not self.data_manager.get_block(block.previous_hash):
                # Postpone processing the current block and request missing blocks
                self.incoming_blocks[block.id] = block
                # TODO: address issues with memory filling up
                self.send_block_request(block.previous_hash)
                self.logger.debug('Postpone block with id %s', b64encode(block.id))
                continue

            if not self.process_block(block):
                continue
            self.logger.debug('Added received block with %s contract(s)', len(block.contracts))
            self.process_blocks_after(block)

    def process_blocks_after(self, block):
        # Process any orphan blocks that depend on the current block
        for orphan in self.incoming_blocks.values():
            if orphan.previous_hash == block.id:
                del self.incoming_blocks[orphan.id]
                if self.process_block(orphan):
                    self.logger.debug('Added postponed block with %s contract(s)', len(orphan.contracts))
                    self.process_blocks_after(orphan)

    def process_block(self, block):
        # We have already checked the proof of this block, but not whether the target_difficulty itself is as expected.
        # Note that we can't to this in check_block, because at that time the previous block may not be known yet.
        prev_block = self.data_manager.get_block(block.previous_hash)
        if block.target_difficulty != self.get_next_difficulty(prev_block):
            self.logger.debug('Block processing failed (unexpected target difficulty)')
            return False

        # Save block
        self.data_manager.add_block(block)

        # Get best chain
        best_chain = self.data_manager.get_best_chain()

        # Calculate height of the chain this block is the head of
        new_height = 1
        cur_block = block
        while cur_block:
            if cur_block.previous_hash == best_chain.block_id:
                new_height += best_chain.height
                break
            cur_block = self.data_manager.get_block(cur_block.previous_hash)
            if cur_block is not None:
                new_height += 1

        # For now, the longest chain wins
        if new_height > best_chain.height:
            best_chain.block_id = block.id
            best_chain.height = new_height

        # Make sure we stop trying to create blocks with the contracts in this block
        for contract in block.contracts:
            if contract.id in self.incoming_contracts:
                del self.incoming_contracts[contract.id]

        return True

    def check_block(self, block):
        if self.get_block_packet_size(block) > MAX_PACKET_SIZE:
            self.logger.debug('Block failed check (block too large)')
            return False

        if not self.check_proof(block):
            # Don't log message when we created the block
            if block.creator != self.my_user_id:
                self.logger.debug('Block failed check (incorrect proof)')
            return False

        if not block.verify():
            self.logger.debug('Block failed check (invalid signature)')
            return False

        if self.data_manager.get_block(block.id):
            self.logger.debug('Block failed check (duplicate block)')
            return False

        if block.time > int(time.time()) + MAX_CLOCK_DRIFT:
            self.logger.debug('Block failed check (max clock drift exceeded)')
            return False

        for contract in block.contracts:
            if block.time < contract.time:
                self.logger.debug('Block failed check (block created before contract)')
                return False

        if len(block.contracts) != len(set([contract.id for contract in block.contracts])):
            self.logger.debug('Block failed check (duplicate contracts)')
            return False

        if block.merkle_root_hash != block.merkle_tree.build():
            self.logger.debug('Block failed check (incorrect merkle root hash)')
            return False

        past_blocks = self.get_past_blocks(block, 11)
        if past_blocks and block.time > median([b.time for b in past_blocks]):
            self.logger.debug('Block failed check (block time larger than median time of past 11 blocks)')
            return False

        return True

    def check_proof(self, block):
        proof = hashlib.sha256(str(block)).digest()
        return bytes_to_uint256(proof) < block.target_difficulty

    def create_block(self):
        best_chain = self.data_manager.get_best_chain()
        prev_block = self.data_manager.get_block(best_chain.block_id)

        block = Block()
        block.previous_hash = prev_block.id if prev_block is not None else BLOCK_GENESIS_HASH
        block.target_difficulty = self.get_next_difficulty(prev_block)
        block.time = int(time.time())

        # Placeholder information (for calculating packet size)
        block.merkle_root_hash = block.merkle_tree.build()
        block.sign(self.my_member)

        # Find dependencies
        contracts = []
        dependencies = {}
        for contract in self.incoming_contracts.values():
            # Get the previous contract from memory or the database
            prev_contract = self.incoming_contracts.get(contract.previous_hash) or \
                            self.data_manager.get_contract(contract.previous_hash) if contract.previous_hash else None

            # We need to wait until the previous contract is received and on the blockchain
            if contract.previous_hash and (prev_contract is None or not prev_contract.block):
                # TODO: support more then 1 previous contract
                dependencies[contract.previous_hash] = contract
            else:
                contracts.append(contract)

        # Add contracts to block
        while contracts:
            contract = contracts.pop()
            block.contracts.append(contract)
            if contract.id in dependencies:
                contracts.insert(0, dependencies[contract.id])

            if self.get_block_packet_size(block) > MAX_PACKET_SIZE:
                block.contracts.pop()
                break

        # Calculate final merkle root hash + sign block
        block.merkle_root_hash = block.merkle_tree.build()
        block.sign(self.my_member)

        if self.check_block(block):
            self.logger.debug('Created block with target difficulty 0x%064x', block.target_difficulty)
            if self.process_block(block):
                self.logger.debug('Added created block with %s contract(s)', len(block.contracts))
                self.multicast_message(u'block', {'block': block.to_dict()}, role=Role.FINANCIAL_INSTITUTION)

    def get_next_difficulty(self, block):
        # Determine difficulty for the next block
        if block is not None:
            target_difficulty = block.target_difficulty

            # Go back BLOCK_TARGET_BLOCKSPAN
            past_blocks = self.get_past_blocks(block, BLOCK_TARGET_BLOCKSPAN)
            if past_blocks:
                target_difficulty *= float(block.time - past_blocks[-1].time) / BLOCK_TARGET_TIMESPAN
        else:
            target_difficulty = BLOCK_DIFFICULTY_INIT

        return min(target_difficulty, BLOCK_DIFFICULTY_MIN)

    def get_past_blocks(self, block, num_past):
        result = []
        current = block
        for _ in range(num_past):
            current = self.data_manager.get_block(current.previous_hash)
            if current is None:
                return None
            result.append(current)
        return result

    def get_block_packet_size(self, block):
        meta = self.get_meta_message(u'block')
        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            destination=(Candidate(('1.1.1.1', 1), False),),
                            payload=({'block': block.to_dict()},))
        return len(message.packet)

    def send_contract(self, document, contract_type, from_id, to_id):
        assert to_id == self.my_user_id or from_id == self.my_user_id

        contract = Contract()
        contract.from_id = from_id
        contract.to_id = to_id
        contract.document = document
        contract.contract_type = contract_type
        contract.time = int(time.time())
        contract.sign(self.my_member)

        return self.send_signature_request(contract)

    def process_contract(self, contract, sign=False):
        # Link to mortgage/investment
        obj = contract.get_object()
        if isinstance(obj, Mortgage):
            # Check if information from the database matches the contract
            mortgage = self.data_manager.get_mortgage(obj.id, obj.user_id)
            if mortgage.to_bin() != contract.document or contract.previous_hash:
                self.logger.warning('Could not process contract (contract does not match mortgage)')
                return False

            # Link to mortgage
            mortgage.contract_id = contract.id

            # Send campaign update
            if self.my_role == Role.FINANCIAL_INSTITUTION:
                campaign = self.data_manager.get_campaign_for_mortgage(mortgage)
                self.send_campaign_update(campaign)

        elif isinstance(obj, Investment):
            # Check if information from the database matches the contract
            investment = self.data_manager.get_investment(obj.id, obj.user_id)
            mortgage = self.data_manager.get_mortgage_for_investment(investment)
            if investment.to_bin() != contract.document or mortgage is None or \
               mortgage.contract_id != contract.previous_hash:
                self.logger.warning('Could not process contract (contract does not match investment)')
                return False

            # Link to investment
            investment.contract_id = contract.id

            # Send campaign update
            if self.my_role == Role.FINANCIAL_INSTITUTION:
                campaign = self.data_manager.get_campaign(investment.campaign_id, investment.campaign_user_id)
                self.send_campaign_update(campaign, investment)

        if sign:
            contract.sign(self.my_member)

        # Add contract to database
        self.data_manager.add_contract(contract)

        return True

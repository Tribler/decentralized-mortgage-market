import os
import time
import base64
import logging
import hashlib

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall

from dispersy.authentication import MemberAuthentication
from dispersy.conversion import DefaultConversion
from dispersy.destination import CommunityDestination, CandidateDestination
from dispersy.distribution import DirectDistribution, FullSyncDistribution
from dispersy.message import Message
from dispersy.resolution import PublicResolution

from internetofmoney.utils.iban import IBANUtil

from market.community.market import accept
from market.community.blockchain.community import BlockchainCommunity
from market.community.market.conversion import MarketConversion
from market.community.payload import ProtobufPayload
from market.database.datamanager import MarketDataManager
from market.models import ObjectType
from market.models.loanrequest import LoanRequest, LoanRequestStatus
from market.models.mortgage import Mortgage, MortgageStatus
from market.models.user import User, Role
from market.models.campaign import Campaign
from market.models.investment import InvestmentStatus, Investment
from market.models.transfer import Transfer, TransferStatus
from market.models.confirmation import Confirmation
from market.models.profile import Profile
from market.models.contract import Contract
from market.restapi.rest_manager import RESTManager
from market.util.uint256 import full_to_uint256
from market.defs import VERIFIED_BANKS

COMMIT_INTERVAL = 60
CLEANUP_INTERVAL = 60
PAYUP_INTERVAL = 30
DEFAULT_CAMPAIGN_DURATION = 30 * 24 * 60 * 60
TRANSFER_LOCK_TIME = 60 * 60
POS_STEP = 1000000
POS_LIMIT = 10 * POS_STEP


class MarketCommunity(BlockchainCommunity):

    def __init__(self, dispersy, master, my_member):
        super(MarketCommunity, self).__init__(dispersy, master, my_member)
        self.logger = logging.getLogger('MarketLogger')
        self.id_to_candidate = {}
        self.rest_manager = None
        self.market_api = None
        self.payment_queue = []
        self.money_community = None
        self.stake_cache = {}

    def initialize(self, rest_api_port=0, role=Role.UNKNOWN, database_fn='', money_community=None):
        super(MarketCommunity, self).initialize(verifier=role == Role.FINANCIAL_INSTITUTION,
                                                role=role, database_fn=database_fn)

        self.money_community = money_community
        self.rest_manager = RESTManager(self, rest_api_port)
        self.market_api = self.rest_manager.start()

        self.register_task('cleanup', LoopingCall(self.cleanup)).start(CLEANUP_INTERVAL)
        self.register_task('payup', LoopingCall(self.payup)).start(PAYUP_INTERVAL)

        self.logger.info('MarketCommunity initialized')
        self.logger.info('Using ID %s', base64.urlsafe_b64encode(self.my_user_id))

    def initialize_database(self, role, database_fn):
        if database_fn:
            database_fn = os.path.join(self.dispersy.working_directory, database_fn)
        self.data_manager = MarketDataManager(database_fn)
        self.data_manager.initialize(self.my_user_id, role)

    def initiate_meta_messages(self):
        meta_messages = super(MarketCommunity, self).initiate_meta_messages()

        return meta_messages + [
            # Message for exchanging user information
            Message(self, u"user",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_user),
            # Agreement messages
            Message(self, u"offer",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_offer),
            Message(self, u"accept",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_accept),
            Message(self, u"reject",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_reject),
            # Notification message
            Message(self, u"campaign-update",
                    MemberAuthentication(),
                    PublicResolution(),
                    FullSyncDistribution(enable_sequence_number=False,
                                         synchronization_direction=u"DESC",
                                         priority=128),
                    CommunityDestination(node_count=10),
                    ProtobufPayload(),
                    self._generic_timeline_check,
                    self.on_campaign_update)
        ]

    def initiate_conversions(self):
        return [DefaultConversion(self), MarketConversion(self)]

    @property
    def my_user_id(self):
        return self.member_to_id(self.my_member)

    def public_key_to_id(self, public_key):
        return hashlib.sha256(public_key).digest()

    def member_to_id(self, member):
        return self.public_key_to_id(member.public_key)

    @inlineCallbacks
    def unload_community(self):
        yield self.rest_manager.stop()
        yield super(MarketCommunity, self).unload_community()

    def cleanup(self):
        for user_id, candidate in self.id_to_candidate.items():
            if candidate.last_walk_reply < time.time() - 300:
                self.id_to_candidate.pop(user_id)

    @inlineCallbacks
    def payup(self):
        self.logger.debug('Payment queue length: %d', len(self.payment_queue))
        for payment in self.payment_queue:
            transfer, investment = payment
            response = yield self.send_traversal_request(investment.contract_id)
            end_of_chain = response[0] if response else None
            if end_of_chain and end_of_chain.id == transfer.contract_id:
                self.logger.debug('Found transfer on blockchain, attempting to pay..')

                # TODO: wait for some number of confirmations

                manager = self.money_community.bank_managers.values()[0]
                source_iban = manager.get_address()
                destination_iban = str(transfer.iban)
                amount = transfer.amount
                candidate = yield self.money_community.has_eligable_router(IBANUtil.get_bank_id(source_iban),
                                                                           IBANUtil.get_bank_id(destination_iban),
                                                                           amount)

                if not candidate:
                    self.logger.error('No eligable money switches found')
                    return

                switch_iban = self.money_community.candidate_services_map[candidate][IBANUtil.get_bank_id(source_iban)]
                self.logger.debug('Moving money from %s to %s through %s', source_iban, destination_iban, switch_iban)

                try:
                    yield self.money_community.send_money_using_router(candidate, manager, amount, switch_iban, destination_iban)

                    self.logger.debug('Payment successful!')
                    self.payment_queue.remove(payment)

                    # Now we need the money router to sign the confirmation contract,
                    # which proves to the network the we have paid
                    confirmation = Confirmation(transfer.id, transfer.user_id, unicode(source_iban),
                                                unicode(destination_iban), amount)
                    document = confirmation.to_bin()

                    self.begin_contract(candidate, document, ObjectType.CONFIRMATION, self.my_member.public_key,
                                        candidate.get_member().public_key, transfer.contract_id)

                except Exception, e:
                    self.logger.error('Error while making payment (%s)', str(e))

    def on_introduction_request(self, messages):
        super(MarketCommunity, self).on_introduction_request(messages)
        for message in messages:
            self.send_user(message.candidate)

    def on_introduction_response(self, messages):
        super(MarketCommunity, self).on_introduction_response(messages)
        for message in messages:
            self.send_user(message.candidate)

    def send_message_to_ids(self, msg_type, user_ids, payload_dict):
        candidates = []
        for user_id in user_ids:
            candidate = self.id_to_candidate.get(user_id)
            if candidate is None:
                self.logger.error('Cannot send %s (unknown user)', msg_type)
                return False
            candidates.append(candidate)
        return self.send_message(msg_type, tuple(candidates), payload_dict)

    def get_verifiers(self):
        # Only financial institutions with stake >= 1 are verifiers on the blockchain
        return [self.id_to_candidate[user.id] for user in self.data_manager.get_users()
                if user.id in self.id_to_candidate \
                and self.get_stake(self.id_to_candidate[user.id].get_member().public_key) >= 1 \
                and user.role == Role.FINANCIAL_INSTITUTION]

    @property
    def my_role(self):
        return self.my_user.role

    @property
    def my_user(self):
        return self.data_manager.get_user(self.my_user_id)

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
        user_id = self.member_to_id(candidate.get_member())
        user = self.data_manager.get_user(user_id)
        if user is not None:
            user.role = role
        else:
            user = User(user_id, role=role)
            self.data_manager.add_user(user)
        self.id_to_candidate[user_id] = candidate
        return user

    def add_or_update_profile(self, candidate, profile):
        user_id = self.member_to_id(candidate.get_member())
        user = self.data_manager.get_user(user_id)
        if profile is not None:
            if user.profile is None:
                user.profile = profile
            else:
                user.profile.merge(profile)

    def _process_user(self, candidate, user_dict):
        user = User.from_dict(user_dict)
        self.add_or_update_user(candidate, role=user.role)

        if 'profile' in user_dict:
            profile = Profile.from_dict(user_dict['profile'])
            self.add_or_update_profile(candidate, profile)
        return user

    def send_user(self, candidate):
        self.send_message(u'user', (candidate,), {'user': self.my_user_dict})

    def on_user(self, messages):
        for message in messages:
            user = self._process_user(message.candidate, message.payload.dictionary['user'])
            self.logger.debug('Got user from %s (role=%s)', message.candidate.sock_addr, user.role)

    def offer_loan_request(self, loan_request):
        return self.send_message_to_ids(u'offer', (loan_request.bank_id,), {'loan_request': loan_request.to_dict(),
                                                                            'profile': self.my_user.profile.to_dict()})

    def reject_loan_request(self, loan_request):
        return self.send_message_to_ids(u'reject', (loan_request.user_id,), {'object_type': ObjectType.LOANREQUEST,
                                                                             'object_id': loan_request.id,
                                                                             'object_user_id': loan_request.user_id})

    def offer_mortgage(self, loan_request, mortgage):
        return self.send_message_to_ids(u'offer', (mortgage.user_id,), {'mortgage': mortgage.to_dict()})

    def accept_mortgage(self, mortgage):
        return self.send_message_to_ids(u'accept', (mortgage.bank_id,), {'object_type': ObjectType.MORTGAGE,
                                                                         'object_id': mortgage.id,
                                                                         'object_user_id': mortgage.user_id})

    def reject_mortgage(self, mortgage):
        return self.send_message_to_ids(u'reject', (mortgage.bank_id,), {'object_type': ObjectType.MORTGAGE,
                                                                         'object_id': mortgage.id,
                                                                         'object_user_id': mortgage.user_id})

    def offer_investment(self, investment):
        campaign = self.data_manager.get_campaign(investment.campaign_id, investment.campaign_user_id)
        if campaign is None:
            self.logger.error('Cannot send investment-offer (unknown campaign)')
            return False

        return self.send_message_to_ids(u'offer', (campaign.user_id,),
                                        {'investment': investment.to_dict(),
                                         'profile': self.data_manager.you.profile.to_dict()})

    def accept_investment(self, investment):
        return self.send_message_to_ids(u'accept', (investment.user_id,),
                                        {'object_type': ObjectType.INVESTMENT,
                                         'object_id': investment.id,
                                         'object_user_id': investment.user_id})

    def reject_investment(self, investment):
        return self.send_message_to_ids(u'reject', (investment.user_id,), {'object_type': ObjectType.INVESTMENT,
                                                                           'object_id': investment.id,
                                                                           'object_user_id': investment.user_id})

    @inlineCallbacks
    def offer_transfer(self, transfer):
        investment = self.data_manager.get_investment(transfer.investment_id, transfer.investment_user_id)
        if investment is None:
            self.logger.error('Cannot send transfer-offer (unknown investment)')
            return

        self.logger.debug('Verifying contract ownership')

        # First, we verify the owner of the investment
        owner_public_key = yield self.find_owner_remote(investment.contract_id)

        if owner_public_key:
            self.logger.debug('Contract ownership verification successful!')

            owner_id = self.public_key_to_id(owner_public_key)
            owner = self.data_manager.get_user(owner_id)

            if owner is None or owner.profile is None or not owner.profile.iban:
                self.logger.warning('Cannot find IBAN of owner')
                return

            transfer.iban = owner.profile.iban
            self.send_message_to_ids(u'offer', (owner_id,),
                                     {'transfer': transfer.to_dict(),
                                      'investment': investment.to_dict()})
        else:
            self.logger.warning('Contract ownership verification failed!')

    def accept_transfer(self, transfer):
        investment = self.data_manager.get_investment(transfer.investment_id, transfer.investment_user_id)
        if investment is None:
            self.logger.error('Cannot send transfer-offer (unknown investment)')
            return False

        return self.send_message_to_ids(u'accept', (transfer.user_id,),
                                        {'object_type': ObjectType.TRANSFER,
                                         'object_id': transfer.id,
                                         'object_user_id': transfer.user_id})

    def reject_transfer(self, transfer):
        return self.send_message_to_ids(u'reject', (transfer.user_id,), {'object_type': ObjectType.TRANSFER,
                                                                         'object_id': transfer.id,
                                                                         'object_user_id': transfer.user_id})

    def on_offer(self, message):
        for message in message:
            dictionary = message.payload.dictionary
            sock_addr = message.candidate.sock_addr

            if set(('loan_request', 'profile')) <= set(dictionary):
                loan_request = LoanRequest.from_dict(dictionary['loan_request'])
                if loan_request is None:
                    self.logger.warning('Dropping invalid loanrequest offer from %s', sock_addr)
                    continue

                self.logger.debug('Got loanrequest offer from %s', sock_addr)
                profile = Profile.from_dict(dictionary['profile'])
                user = self.add_or_update_user(message.candidate, role=Role.BORROWER)
                self.add_or_update_profile(message.candidate, profile)
                user.loan_requests.add(loan_request)

            elif set(('mortgage',)) <= set(dictionary):
                mortgage = Mortgage.from_dict(dictionary['mortgage'])
                if mortgage is None:
                    self.logger.warning('Dropping invalid mortgage offer from %s', sock_addr)
                    continue
                elif mortgage.bank_id != self.member_to_id(message.candidate.get_member()):
                    self.logger.warning('Dropping mortgage offer from %s (wrong sender)', sock_addr)
                    continue

                loan_request = self.data_manager.get_loan_request(mortgage.loan_request_id, mortgage.loan_request_user_id)
                if not loan_request:
                    self.logger.warning('Dropping mortgage offer from %s (unknown loan request)', sock_addr)
                    continue

                self.logger.debug('Got mortgage offer from %s', sock_addr)
                self.add_or_update_user(message.candidate, role=Role.FINANCIAL_INSTITUTION)
                loan_request.status = LoanRequestStatus.ACCEPTED
                loan_request.mortgage = mortgage
                self.data_manager.you.mortgages.add(mortgage)

            elif set(('investment', 'profile')) <= set(dictionary):
                investment = Investment.from_dict(dictionary['investment'])
                campaign = self.data_manager.get_campaign(investment.campaign_id, investment.campaign_user_id)
                if campaign is None:
                    self.logger.warning('Dropping investment offer from %s (unknown campaign)', sock_addr)
                    continue
                elif campaign.amount_invested + investment.amount > campaign.amount:
                    self.logger.warning('Auto-rejecting investment offer from %s (amount too large)', sock_addr)
                    self.reject_investment(investment)
                    continue

                self.logger.debug('Got investment offer from %s', sock_addr)
                profile = Profile.from_dict(dictionary['profile'])
                self.add_or_update_profile(message.candidate, profile)
                campaign.investments.add(investment)

            elif set(('transfer', 'investment')) <= set(dictionary):
                transfer = Transfer.from_dict(dictionary['transfer'])
                investment = Investment.from_dict(dictionary['investment'])
                if transfer is None or investment is None:
                    self.logger.warning('Dropping invalid transfer offer from %s', sock_addr)
                    continue

                investment = self.data_manager.get_investment(investment.id, investment.user_id)
                if investment is None:
                    self.logger.warning('Dropping transfer offer from %s (unknown investment)', sock_addr)
                    continue

                self.logger.debug('Got transfer offer from %s', sock_addr)

                investment.transfers.add(transfer)

            else:
                self.logger.warning('Dropping offer from %s (unexpected payload)', message.candidate.sock_addr)

    @inlineCallbacks
    def on_accept(self, messages):
        for message in messages:
            dictionary = message.payload.dictionary
            sock_addr = message.candidate.sock_addr

            if dictionary['object_type'] == ObjectType.MORTGAGE:
                mortgage = self.data_manager.get_mortgage(dictionary['object_id'], dictionary['object_user_id'])
                if mortgage is None:
                    self.logger.warning('Dropping mortgage accept from %s (unknown mortgage)', sock_addr)
                    continue

                self.logger.debug('Got mortgage accept from %s', sock_addr)
                mortgage.status = MortgageStatus.ACCEPTED
                self.begin_contract(message.candidate, mortgage.to_bin(), ObjectType.MORTGAGE,
                                    self.my_member.public_key, message.candidate.get_member().public_key)

                # Create campaign
                end_time = int(time.time()) + DEFAULT_CAMPAIGN_DURATION
                finance_goal = mortgage.amount - mortgage.bank_amount
                campaign = Campaign(self.data_manager.you.campaigns.count(), self.my_user_id,
                                    mortgage.id, mortgage.user_id, finance_goal, 0, end_time)
                self.data_manager.you.campaigns.add(campaign)

            elif dictionary['object_type'] == ObjectType.INVESTMENT:
                investment = self.data_manager.get_investment(dictionary['object_id'], dictionary['object_user_id'])
                if investment is None:
                    self.logger.warning('Dropping investment accept from %s (unknown investment)', sock_addr)
                    continue

                campaign = self.data_manager.get_campaign(investment.campaign_id, investment.campaign_user_id)
                if campaign is None:
                    self.logger.warning('Dropping investment accept from %s (unknown campaign)', sock_addr)
                    continue

                mortgage = self.data_manager.get_mortgage_for_investment(investment)
                if mortgage is None:
                    self.logger.warning('Dropping investment accept from %s (unknown mortgage)', sock_addr)
                    continue

                self.logger.debug('Got investment accept from %s', sock_addr)
                investment.status = InvestmentStatus.ACCEPTED
                campaign.amount_invested += investment.amount
                self.begin_contract(message.candidate, investment.to_bin(), ObjectType.INVESTMENT,
                                    message.candidate.get_member().public_key, self.my_member.public_key,
                                    mortgage.contract_id)

            elif dictionary['object_type'] == ObjectType.TRANSFER:
                transfer = self.data_manager.get_transfer(dictionary['object_id'], dictionary['object_user_id'])
                if transfer is None:
                    self.logger.warning('Dropping transfer accept from %s (unknown transfer)', sock_addr)
                    continue

                investment = self.data_manager.get_investment(transfer.investment_id, transfer.investment_user_id)
                if investment is None:
                    self.logger.warning('Dropping transfer accept from %s (unknown investment)', sock_addr)
                    continue

                self.logger.debug('Got transfer accept from %s', sock_addr)
                transfer.status = TransferStatus.ACCEPTED

                response = yield self.send_traversal_request(investment.contract_id)
                if response is not None:
                    prev_contract, _ = response
                    self.begin_contract(message.candidate, transfer.to_bin(), ObjectType.TRANSFER,
                                        message.candidate.get_member().public_key, self.my_member.public_key,
                                        prev_contract.id)
                else:
                    self.logger.error('Could not find previous contract will attempting to create a transfer contract')

            else:
                self.logger.warning('Dropping accept from %s (unknown object_type)', sock_addr)

    def on_reject(self, messages):
        for message in messages:
            dictionary = message.payload.dictionary
            sock_addr = message.candidate.sock_addr

            if dictionary['object_type'] == ObjectType.LOANREQUEST:
                loanrequest = self.data_manager.get_loan_request(dictionary['object_id'], dictionary['object_user_id'])
                if loanrequest is None:
                    self.logger.warning('Dropping loanrequest reject from %s (unknown loanrequest)', sock_addr)
                    continue

                self.logger.debug('Got loanrequest reject from %s', sock_addr)
                loanrequest.status = LoanRequestStatus.REJECTED

            elif dictionary['object_type'] == ObjectType.MORTGAGE:
                mortgage = self.data_manager.get_mortgage(dictionary['object_id'], dictionary['object_user_id'])
                if mortgage is None:
                    self.logger.warning('Dropping mortgage reject from %s (unknown mortgage)', sock_addr)
                    continue

                self.logger.debug('Got mortgage reject from %s', sock_addr)
                mortgage.status = MortgageStatus.REJECTED

            elif dictionary['object_type'] == ObjectType.INVESTMENT:
                investment = self.data_manager.get_investment(dictionary['object_id'], dictionary['object_user_id'])
                if investment is None:
                    self.logger.warning('Dropping investment reject from %s (unknown investment)', sock_addr)
                    continue

                self.logger.debug('Got investment reject from %s', sock_addr)
                investment.status = InvestmentStatus.REJECTED

            elif dictionary['object_type'] == ObjectType.TRANSFER:
                transfer = self.data_manager.get_transfer(dictionary['object_id'], dictionary['object_user_id'])
                if transfer is None:
                    self.logger.warning('Dropping transfer accept from %s (unknown transfer)', sock_addr)
                    continue

                self.logger.debug('Got transfer reject from %s', sock_addr)
                transfer.status = TransferStatus.REJECTED

            else:
                self.logger.warning('Dropping reject from %s (unknown object_type)', sock_addr)

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
        return self.dispersy.store_update_forward([message], True, True, True)

    def on_campaign_update(self, messages):
        for message in messages:
            dictionary = message.payload.dictionary

            if set(('campaign', 'mortgage')) == set(dictionary):
                # Campaign update. Informs us about how much money the bank still needs.
                campaign = Campaign.from_dict(dictionary['campaign'])
                mortgage = Mortgage.from_dict(dictionary['mortgage'])

                if campaign is None or mortgage is None:
                    self.logger.warning('Dropping invalid campaign-update from %s', message.candidate.sock_addr)
                    continue

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
                    existing_campaign.amount_invested = max(existing_campaign.amount_invested, campaign.amount_invested)

            elif set(('campaign', 'mortgage', 'investment')) == set(dictionary):
                # Someone is offering an investment that they own for resale
                campaign = Campaign.from_dict(dictionary['campaign'])
                mortgage = Mortgage.from_dict(dictionary['mortgage'])
                investment = Investment.from_dict(dictionary['investment'])

                if campaign is None or mortgage is None or investment is None:
                    self.logger.warning('Dropping invalid campaign-update from %s', message.candidate.sock_addr)
                    continue

                bank = self.data_manager.get_user(campaign.user_id)
                if bank is None:
                    self.logger.warning('Dropping campaign-update (unknown user_id)')
                    continue

                self.logger.debug('Got campaign-update (for investment)')

                user = self.data_manager.get_user(mortgage.user_id)
                if user is None:
                    user = User(mortgage.user_id, role=Role.BORROWER)
                    self.data_manager.add_user(user)

                # TODO: check if this message is signed by the investment owner

                if self.data_manager.get_mortgage(mortgage.id, mortgage.user_id) is None:
                    user.mortgages.add(mortgage)

                existing_campaign = self.data_manager.get_campaign(campaign.id, campaign.user_id)
                if existing_campaign is None:
                    bank.campaigns.add(campaign)
                else:
                    campaign = existing_campaign

                existing_investment = self.data_manager.get_investment(investment.id, investment.user_id)
                if existing_investment is None:
                    campaign.investments.add(investment)
                else:
                    # Update the existing investment with the new status. Should be either ACCEPTED or FORSALE
                    existing_investment.status = investment.status

    def get_stake(self, public_key):
        for key, (ts, _) in self.stake_cache.items():
            # Remove entries that are older than 1h
            if ts > time.time() + 3600:
                del self.stake_cache[key]

        if public_key not in self.stake_cache:
            value = 0

            contracts = self.data_manager.find_contracts(Contract.to_public_key == public_key,
                                                         Contract.type in [ObjectType.INVESTMENT, ObjectType.TRANSFER])

            for contract in contracts:
                if not self.data_manager.contract_on_blockchain(contract.id):
                    continue

                # Find the mortgage contract
                root_contract = contract
                while root_contract.type != ObjectType.MORTGAGE:
                    root_contract = self.data_manager.get_contract(root_contract.previous_hash)

                # Only consider contracts that are linked to a mortgage contract by a verified bank
                if root_contract and root_contract.type == ObjectType.MORTGAGE and root_contract.to_public_key in VERIFIED_BANKS.values():
                    # Calculate the value the peer has on the network
                    if self.find_owner(contract.id) == public_key:
                        value += contract.get_object().amount


            #  Give stake a +1 for every POS_STEP invested. Consider amounts up to POS_LIMIT.
            stake = min(value, POS_LIMIT) / POS_STEP

            # To allow bootstrapping we give verified banks a minimum stake of 1
            if public_key in VERIFIED_BANKS.values():
                stake = max(stake, 1)

            self.stake_cache[public_key] = (time.time(), stake)

        return self.stake_cache[public_key][1]

    def check_proof(self, block):
        proof = hashlib.sha256(str(block)).digest()
        stake = self.get_stake(block.creator)
        return full_to_uint256(proof) < (block.target_difficulty * stake)

    def check_contract(self, contract, fail_without_parent=True):
        if not super(MarketCommunity, self).check_contract(contract, fail_without_parent=fail_without_parent):
            return False

        if contract.previous_hash:
            prev_contract = self.incoming_contracts.get(contract.previous_hash) or \
                            self.data_manager.get_contract(contract.previous_hash)

            if prev_contract is None:
                # Should never happen since BlockchainCommunity.check_contract also checks for this
                return True

            elif (prev_contract.type == ObjectType.MORTGAGE and contract.type != ObjectType.INVESTMENT) or \
                 (prev_contract.type == ObjectType.INVESTMENT and contract.type != ObjectType.TRANSFER) or \
                 (prev_contract.type == ObjectType.TRANSFER and contract.type not in [ObjectType.TRANSFER, ObjectType.CONFIRMATION]) or \
                 (prev_contract.type == ObjectType.CONFIRMATION and contract.type != ObjectType.TRANSFER):
                self.logger.debug('Contract failed check (unexpected contract type)')
                return False

            elif contract.type not in [ObjectType.MORTGAGE, ObjectType.INVESTMENT] and self.has_sibling(contract):
                self.logger.debug('Contract failed check (attempt to double spend)')
                return False

            elif contract.type == ObjectType.TRANSFER:
                if prev_contract == ObjectType.TRANSFER:
                    block_id = self.data_manager.get_blockchain_block_id(prev_contract.id)
                    block = self.data_manager.get_block(block_id)
                    if block is None:
                        self.logger.debug('Contract failed check (previous transfer not on blockchain)')
                        return False
                    elif time.time() < block.time + TRANSFER_LOCK_TIME:
                        self.logger.debug('Contract failed check (time between transfers too short)')
                        return False

                investment_contract = self.find_investment_contract(contract)
                if not investment_contract:
                    self.logger.debug('Contract failed check (unable to find investment contract)')
                    return False
                elif self.find_owner(investment_contract.id) != contract.from_public_key:
                    self.logger.debug('Contract failed check (unauthorized)')
                    return False

            elif contract.type == ObjectType.INVESTMENT:
                # Find all contracts that depend on this mortgage
                contracts = self.data_manager.find_contracts(Contract.previous_hash == prev_contract.id)
                contracts = list(contracts) if contracts.count() > 0 else []
                contracts += [c for c in self.incoming_contracts.values()
                              if c.previous_hash == prev_contract.id]
                contracts.append(contract)

                # Filter out duplicates
                contracts_dict = {}
                for contract in contracts:
                    contracts_dict[contract.id] = contract
                contracts = contracts_dict.values()

                # Make sure the sum of all investments does not surpass the maximum allowed amount
                mortgage = prev_contract.get_object()
                maximum_value = mortgage.amount - mortgage.bank_amount
                current_value = sum([c.get_object().amount for c in contracts
                                     if c.type == ObjectType.INVESTMENT])

                if current_value > maximum_value:
                    self.logger.debug('Contract failed check (attempt to overspend)')
                    return False

            elif contract.type == ObjectType.CONFIRMATION:
                # TODO: check confirmation
                pass

        return True

    def has_sibling(self, contract):
        for c in self.incoming_contracts.itervalues():
            if c.id != contract.id and c.previous_hash == contract.previous_hash:
                return True

        # For some reason if we add Contract.id != contract.id to the find_contract arguments,
        # it may still produce results where Contract.id == contract.id. So we check this manually.
        contracts = self.data_manager.find_contracts(Contract.previous_hash == contract.previous_hash)
        for c in list(contracts):
            if c.id != contract.id:
                return True

        return False

    def finalize_contract(self, contract, sign=False):
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
                self.send_campaign_update(campaign)

        elif isinstance(obj, Transfer):
            # Check if information from the database matches the contract
            # TODO: check previous hash
            transfer = self.data_manager.get_transfer(obj.id, obj.user_id)
            if transfer.to_bin() != contract.document:
                self.logger.warning('Could not process contract (contract does not match transfer)')
                return False

            # Link to transfer
            transfer.contract_id = contract.id

            # Send campaign update
            # TODO
            investment = self.data_manager.get_investment(transfer.investment_id, transfer.investment_user_id)
            campaign = self.data_manager.get_campaign(investment.campaign_id, investment.campaign_user_id)
            investment.status = InvestmentStatus.ACCEPTED
            if transfer.user_id != self.my_user_id:
                self.send_campaign_update(campaign, investment)
                self.data_manager.you.investments.remove(investment)
            else:
                self.data_manager.you.investments.add(investment)

                # After this contract is added to the blockchain, we will need to pay
                self.logger.debug('Adding item to payment queue')
                self.payment_queue.append((transfer, investment))

        elif isinstance(obj, Confirmation):
            # Link to transfer
            transfer = self.data_manager.get_transfer(obj.transfer_id, obj.transfer_user_id)
            if transfer is not None:
                transfer.confirmation_contract_id = contract.id
            # TODO: check if we have routed the money

        return super(MarketCommunity, self).finalize_contract(contract, sign=sign)

    @inlineCallbacks
    def find_owner_remote(self, contract_id):
        response = yield self.send_traversal_request(contract_id, ObjectType.CONFIRMATION)
        if response is None or response[0] is None:
            response = yield self.send_traversal_request(contract_id, ObjectType.INVESTMENT)
            owner = response[0].to_public_key if response else None
        else:
            contract, _ = response
            owner = contract.from_public_key

        returnValue(owner)

    def find_owner(self, contract_id):
        contract = self.traverse_contracts(contract_id, ObjectType.CONFIRMATION)

        if not contract:
            contract = self.traverse_contracts(contract_id, ObjectType.INVESTMENT)
            return contract.to_public_key if contract else None
        else:
            return contract.from_public_key

    def find_investment_contract(self, contract):
        # Go up in the chain until we find the investment
        while contract and contract.type != ObjectType.INVESTMENT:
            contract = self.data_manager.get_contract(contract.previous_hash)
        return contract

    # Make sure we only accept blockchain messages if the sender is a financial institution with stake >= 1

    @accept(local=Role.FINANCIAL_INSTITUTION)
    def on_contract(self, messages):
        super(MarketCommunity, self).on_contract(messages)

    @accept(local=Role.FINANCIAL_INSTITUTION, remote=Role.FINANCIAL_INSTITUTION)
    def on_block_request(self, messages):
        super(MarketCommunity, self).on_block_request(messages)

    @accept(local=Role.FINANCIAL_INSTITUTION, remote=Role.FINANCIAL_INSTITUTION)
    def on_block(self, messages):
        super(MarketCommunity, self).on_block(messages)

    @accept(local=Role.FINANCIAL_INSTITUTION)
    def on_traversal_request(self, messages):
        super(MarketCommunity, self).on_traversal_request(messages)

    @accept(remote=Role.FINANCIAL_INSTITUTION)
    def on_traversal_response(self, messages):
        super(MarketCommunity, self).on_traversal_response(messages)

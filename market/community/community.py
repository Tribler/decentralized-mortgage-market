import base64
import logging
import time

from market.dispersy.community import Community
from market.dispersy.conversion import DefaultConversion
from market.dispersy.destination import CommunityDestination, CandidateDestination
from market.dispersy.distribution import DirectDistribution, FullSyncDistribution
from market.dispersy.message import Message, DelayMessageByProof
from market.dispersy.resolution import PublicResolution
from market.dispersy.authentication import MemberAuthentication, DoubleMemberAuthentication

from twisted.internet import reactor
from twisted.web import server

from conversion import MortgageConversion
from payload import MortgageIntroductionRequestPayload, MortgageIntroductionResponsePayload

from market import Global
from market.api.api import STATUS
from market.api.datamanager import MarketDataManager
from market.defs import REST_API_ENABLED, REST_API_PORT
from market.models import DatabaseModel
from market.models.house import House
from market.models.loanrequest import LoanRequest
from market.models.mortgage import Mortgage
from market.models.campaign import Campaign
from market.models.investment import Investment
from market.models.profile import BorrowersProfile, Profile
from market.models.user import User
from market.database.backends import DatabaseBlock, BlockChain
from market.restapi.root_endpoint import RootEndpoint
from market.community import *


class MortgageSettings(object):

    def __init__(self):
        self.user_type = USER_TYPE_INVESTOR


class MortgageCommunity(Community):

    def __init__(self, dispersy, master, my_member):
        super(MortgageCommunity, self).__init__(dispersy, master, my_member)
        self.logger = logging.getLogger(__name__)
        self._api = None
        self._user = None
        self.market_api = None
        self.data_manager = MarketDataManager()

    def initialize(self, settings=None):
        super(MortgageCommunity, self).initialize()

        self.settings = settings or MortgageSettings()

        # Start the RESTful API if it's enabled
        if REST_API_ENABLED:
            self.market_api = reactor.listenTCP(REST_API_PORT, server.Site(resource=RootEndpoint(self)))

        self.logger.info("MortgageCommunity initialized")

        # TEST USER..
        self.user = User(self.my_member.public_key.encode('hex'))

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
        master_key = "3081a7301006072a8648ce3d020106052b81040027038192000407bacf5ae4d3fe94d49a7f94b7239e9c2d878b29f0fbdb7374d5b6a09d9d6fba80d3807affd0ba45ba1ac1c278ca59bec422d8a44b5fefaabcdd62c2778414c01da4578b304b104b00eec74de98dcda803b79fd1783d76cc1bd7aab75cfd8fff9827a9647ae3c59423c2a9a984700e7cb43b881a6455574032cc11dba806dba9699f54f2d30b10eed5c7c0381a0915a5".decode("HEX")
        master = dispersy.get_member(public_key=master_key)
        return [master]

    def initiate_meta_messages(self):
        meta_messages = super(MortgageCommunity, self).initiate_meta_messages()
        for i, mm in enumerate(meta_messages):
            if mm.name == "dispersy-introduction-request":
                meta_messages[i] = Message(self, mm.name, mm.authentication, mm.resolution, mm.distribution,
                                           mm.destination, MortgageIntroductionRequestPayload(),
                                           mm.check_callback, mm.handle_callback)
            elif mm.name == "dispersy-introduction-response":
                meta_messages[i] = Message(self, mm.name, mm.authentication, mm.resolution, mm.distribution,
                                           mm.destination, MortgageIntroductionResponsePayload(),
                                           mm.check_callback, mm.handle_callback)

        return meta_messages + [Message(self, u"loan-request",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        LoanRequestPayload(),
                                        self._generic_timeline_check,
                                        self.on_loan_request),
                                Message(self, u"loan-reject",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        LoanRequestRejectPayload(),
                                        self._generic_timeline_check,
                                        self.on_loan_reject),
                                Message(self, u"mortgage-offer",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        MortgageOfferPayload(),
                                        self._generic_timeline_check,
                                        self.on_mortgage_offer),
                                Message(self, u"mortgage-accept",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        MortgageAcceptSignedPayload(),
                                        self._generic_timeline_check,
                                        self.on_mortgage_accept),
                                Message(self, u"mortgage-reject",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        MortgageRejectPayload(),
                                        self._generic_timeline_check,
                                        self.on_mortgage_reject),
                                Message(self, u"investment-offer",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        InvestmentOfferPayload(),
                                        self._generic_timeline_check,
                                        self.on_investment_offer),
                                Message(self, u"investment-accept",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        InvestmentAcceptPayload(),
                                        self._generic_timeline_check,
                                        self.on_investment_accept),
                                Message(self, u"investment-reject",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        MortgageAcceptSignedPayload(),
                                        self._generic_timeline_check,
                                        self.on_investment_reject),
                                Message(self, u"campaign-bid",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        FullSyncDistribution(enable_sequence_number=False, synchronization_direction=u"DESC", priority=128),
                                        CommunityDestination(node_count=10),
                                        CampaignBidPayload(),
                                        self._generic_timeline_check,
                                        self.on_campaign_bid),
                                Message(self, u"signed-confirm",
                                        DoubleMemberAuthentication(allow_signature_func=self.allow_signed_confirm_request),
                                        PublicResolution(),
                                        DirectDistribution(),
                                        CandidateDestination(),
                                        SignedConfirmPayload(),
                                        self._generic_timeline_check,
                                        self.on_signed_confirm_response)]

    def initiate_conversions(self):
        return [DefaultConversion(self), MortgageConversion(self)]

    def on_introduction_request(self, messages):
        extra_payload = [self.user]
        super(MortgageCommunity, self).on_introduction_request(messages, extra_payload)
        for message in messages:
            self.update_exit_candidates(message.candidate, message.payload.exitnode)

    def create_introduction_request(self, destination, allow_sync, forward=True, is_fast_walker=False):
        extra_payload = [self.user]
        super(MortgageCommunity, self).create_introduction_request(destination, allow_sync, forward,
                                                                   is_fast_walker, extra_payload)

    def on_introduction_response(self, messages):
        super(MortgageCommunity, self).on_introduction_response(messages)
        for message in messages:
            self.update_exit_candidates(message.candidate, message.payload.exitnode)

    def on_loan_request(self, message):
        for message in message:
            pass

    def on_loan_reject(self, message):
        for message in message:
            pass

    def on_mortgage_offer(self, message):
        for message in message:
            pass

    def on_mortgage_accept(self, message):
        for message in message:
            pass

    def on_mortgage_reject(self, message):
        for message in message:
            pass

    def on_investment_offer(self, message):
        for message in message:
            pass

    def on_investment_accept(self, message):
        for message in message:
            pass

    def on_investment_reject(self, message):
        for message in message:
            pass

    def on_campaign_bid(self, message):
        for message in message:
            pass

    def on_signed_confirm_response(self, message):
        for message in message:
            pass

    def send_loan_request(self, loan_request, house, borrowers_profile):
           pass

    def send_loan_reject(self, load_request):
           pass

    def send_mortgage_offer(self, load_request, mortgage):
           pass

    def send_mortgage_accept(self, mortgage, campaign):
           pass

    def send_mortgage_reject(self, mortgage):
           pass

    def send_investment_offer(self, investment, invester_profile):
           pass

    def send_investment_accept(self, investment, borrower_profile):
           pass

    def send_investment_reject(self, investment):
           pass

    def send_campaign_bid(self, investment, campaign, loan_request, house, mortgage):
           pass

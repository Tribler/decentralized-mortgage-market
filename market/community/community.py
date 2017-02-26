import logging

from market.dispersy.community import Community
from market.dispersy.conversion import DefaultConversion
from market.dispersy.destination import CommunityDestination, CandidateDestination
from market.dispersy.distribution import DirectDistribution, FullSyncDistribution
from market.dispersy.message import Message
from market.dispersy.resolution import PublicResolution
from market.dispersy.authentication import MemberAuthentication, DoubleMemberAuthentication

from twisted.internet import reactor
from twisted.web import server

from conversion import MortgageConversion
from market.models.user import User
from payload import MortgageIntroductionRequestPayload, MortgageIntroductionResponsePayload

# from market.api.api import STATUS
from market.api.datamanager import MarketDataManager
from market.defs import REST_API_ENABLED, REST_API_PORT
# from market.database.backends import DatabaseBlock, BlockChain
from market.restapi.root_endpoint import RootEndpoint

from market.community import ROLE_INVESTOR, ROLE_BANK
from market.community.payload import ProtobufPayload


class MortgageSettings(object):

    def __init__(self):
        self.role = ROLE_INVESTOR


class MortgageCommunity(Community):

    def __init__(self, dispersy, master, my_member):
        super(MortgageCommunity, self).__init__(dispersy, master, my_member)
        self.logger = logging.getLogger('MortgageLogger')
        self._api = None
        self._user = None
        self.market_api = None
        self.data_manager = MarketDataManager(User(None))

    def initialize(self, settings=None):
        super(MortgageCommunity, self).initialize()

        self.settings = settings or MortgageSettings()

        # Start the RESTful API if it's enabled
        if REST_API_ENABLED:
            self.market_api = reactor.listenTCP(REST_API_PORT, server.Site(resource=RootEndpoint(self)))

        self.logger.info("MortgageCommunity initialized")

        # SOME TESTING CODE..
        self.users = {}
        self.my_user = {'user_id': self.my_member.public_key.encode('hex'),
                        'role': self.settings.role,
                        'profile': {'first_name': 'firstname',
                                    'last_name': 'lastname',
                                    'email': 'email',
                                    'iban': 'iban',
                                    'phone_number': 'phone'}}

        loan_request = {'user_id': '123',
                        'house_id': '0',
                        'mortgage_type': 0,
                        'banks': [''],
                        'description': '',
                        'amount_wanted': 0,
                        'status': ''}

        house = {'postal_code': '',
                 'house_number': '',
                 'address': '',
                 'price': 0,
                 'url': '',
                 'seller_phone_number': '',
                 'seller_email': ''}

        borrowers_profile = {'profile': {'first_name': '',
                                          'last_name': '',
                                          'email': '',
                                          'iban': '',
                                          'phone_number': ''},
                             'current_postal_code': '',
                             'current_house_number': '',
                             'current_address': '',
                             'document_list': ['']}

        reactor.callLater(300, self.send_loan_request, loan_request, house, borrowers_profile)

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
                                Message(self, u"campaign-bid",
                                        MemberAuthentication(),
                                        PublicResolution(),
                                        FullSyncDistribution(enable_sequence_number=False, synchronization_direction=u"DESC", priority=128),
                                        CommunityDestination(node_count=10),
                                        ProtobufPayload(),
                                        self._generic_timeline_check,
                                        self.on_campaign_bid)]
#                                 Message(self, u"signed-confirm",
#                                         DoubleMemberAuthentication(allow_signature_func=self.allow_signed_confirm_request),
#                                         PublicResolution(),
#                                         DirectDistribution(),
#                                         CandidateDestination(),
#                                         SignedConfirmPayload(),
#                                         self._generic_timeline_check,
#                                         self.on_signed_confirm_response)]

    def initiate_conversions(self):
        return [DefaultConversion(self), MortgageConversion(self)]

    def on_introduction_request(self, messages):
        for message in messages:
            self.logger.debug('Got intro-request from %s (role=%d)', message.candidate, message.payload.user['role'])
            self.users[message.candidate] = message.payload.user
        super(MortgageCommunity, self).on_introduction_request(messages, [self.my_user])

    def create_introduction_request(self, destination, allow_sync, forward=True, is_fast_walker=False):
        self.logger.debug('Sending intro-request to %s', destination)
        super(MortgageCommunity, self).create_introduction_request(destination, allow_sync, forward,
                                                                   is_fast_walker, [self.my_user])

    def on_introduction_response(self, messages):
        for message in messages:
            self.logger.debug('Got intro-response from %s (role=%d)', message.candidate.sock_addr, message.payload.user['role'])
            self.users[message.candidate] = message.payload.user
        super(MortgageCommunity, self).on_introduction_response(messages)

    def on_loan_request(self, message):
        for message in message:
            self.logger.debug('Got loan-request from %s', message.candidate.sock_addr)

    def on_loan_reject(self, message):
        for message in message:
            self.logger.debug('Got loan-reject from %s', message.candidate.sock_addr)

    def on_mortgage_offer(self, message):
        for message in message:
            self.logger.debug('Got mortgage-offer from %s', message.candidate.sock_addr)

    def on_mortgage_accept(self, message):
        for message in message:
            self.logger.debug('Got mortgage-accept from %s', message.candidate.sock_addr)

    def on_mortgage_reject(self, message):
        for message in message:
            self.logger.debug('Got mortgage-reject from %s', message.candidate.sock_addr)

    def on_investment_offer(self, message):
        for message in message:
            self.logger.debug('Got investment-offer from %s', message.candidate.sock_addr)

    def on_investment_accept(self, message):
        for message in message:
            self.logger.debug('Got investment-accept from %s', message.candidate.sock_addr)

    def on_investment_reject(self, message):
        for message in message:
            self.logger.debug('Got investment-reject from %s', message.candidate.sock_addr)

    def on_campaign_bid(self, message):
        for message in message:
            self.logger.debug('Got campaign-bid from %s', message.candidate.sock_addr)

    def on_signed_confirm_response(self, message):
        for message in message:
            self.logger.debug('Got signed-confirm-response from %s', message.candidate.sock_addr)

    def send_loan_request(self, loan_request, house, borrowers_profile):
        msg_dict = {'loan_request': loan_request,
                    'house': house,
                    'borrowers_profile': borrowers_profile}

        meta = self.get_meta_message(u"loan-request")
        message = meta.impl(authentication=(self.my_member,),
                            distribution=(self.claim_global_time(),),
                            destination=tuple([c for c, u in self.users.iteritems() if u['role'] & ROLE_BANK]),
                            payload=(msg_dict,))
        self.dispersy.store_update_forward([message], False, False, True)

    def send_loan_reject(self, loan_request):
           pass

    def send_mortgage_offer(self, loan_request, mortgage):
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



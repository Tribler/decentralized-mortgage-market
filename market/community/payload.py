import mortgage_pb2 as pb

from market.dispersy.payload import Payload, IntroductionRequestPayload, IntroductionResponsePayload


class MortgageIntroductionRequestPayload(IntroductionRequestPayload):

    class Implementation(IntroductionRequestPayload.Implementation):

        def __init__(self, meta, destination_address, source_lan_address, source_wan_address, advice, connection_type, sync, identifier, user=None):
            super(MortgageIntroductionRequestPayload.Implementation, self).__init__(meta, destination_address, source_lan_address, source_wan_address, advice, connection_type, sync, identifier)
            self._user = user

        @property
        def user(self):
            return self._user


class MortgageIntroductionResponsePayload(IntroductionResponsePayload):

    class Implementation(IntroductionResponsePayload.Implementation):

        def __init__(self, meta, destination_address, source_lan_address, source_wan_address, lan_introduction_address, wan_introduction_address, connection_type, tunnel, identifier, user=None):
            super(MortgageIntroductionResponsePayload.Implementation, self).__init__(meta, destination_address, source_lan_address, source_wan_address, lan_introduction_address, wan_introduction_address, connection_type, tunnel, identifier)
            self._user = user

        @property
        def user(self):
            return self._user


class LoanRequestPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, investment, campaign, loan_request, house, borrowers_profile):
            assert isinstance(loan_request, pb.LoanRequest), type(loan_request)
            assert isinstance(house, pb.House), type(house)
            assert isinstance(borrowers_profile, pb.BorrowersProfile), type(borrowers_profile)

            super(Payload.Implementation, self).__init__(meta)
            self._loan_request = loan_request
            self._house = house
            self._borrowers_profile = borrowers_profile

        @property
        def loan_request(self):
            return self._loan_request

        @property
        def house(self):
            return self._house

        @property
        def borrowers_profile(self):
            return self._borrowers_profile


class LoanRejectPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, loan_request):
            assert isinstance(loan_request, pb.LoanRequest), type(loan_request)

            super(Payload.Implementation, self).__init__(meta)
            self._loan_request = loan_request

        @property
        def loan_request(self):
            return self._loan_request


class MortgageOfferPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, loan_request, mortgage):
            assert isinstance(loan_request, pb.LoanRequest), type(loan_request)
            assert isinstance(mortgage, pb.Mortgage), type(mortgage)

            super(Payload.Implementation, self).__init__(meta)
            self._loan_request = loan_request
            self._mortgage = mortgage

        @property
        def loan_request(self):
            return self._loan_request

        @property
        def mortgage(self):
            return self._mortgage


class MortgageAcceptPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, campaign, mortgage):
            assert isinstance(campaign, pb.Campaign), type(campaign)
            assert isinstance(mortgage, pb.Mortgage), type(mortgage)

            super(Payload.Implementation, self).__init__(meta)
            self._campaign = campaign
            self._mortgage = mortgage

        @property
        def campaign(self):
            return self._campaign

        @property
        def mortgage(self):
            return self._mortgage


class MortgageRejectPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, mortgage):
            assert isinstance(mortgage, pb.Mortgage), type(mortgage)

            super(Payload.Implementation, self).__init__(meta)
            self._mortgage = mortgage

        @property
        def mortgage(self):
            return self._mortgage


class InvestmentOfferPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, investment, ivestor_profile):
            assert isinstance(investment, pb.Investment), type(investment)
            assert isinstance(ivestor_profile, pb.Profile), type(ivestor_profile)

            super(Payload.Implementation, self).__init__(meta)
            self._investment = investment
            self._ivestor_profile = ivestor_profile

        @property
        def investment(self):
            return self._investment

        @property
        def ivestor_profile(self):
            return self._ivestor_profile


class InvestmentAcceptPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, investment, borrowers_profile):
            assert isinstance(investment, pb.Investment), type(investment)
            assert isinstance(borrowers_profile, pb.BorrowersProfile), type(borrowers_profile)

            super(Payload.Implementation, self).__init__(meta)
            self._investment = investment
            self._borrowers_profile = borrowers_profile

        @property
        def investment(self):
            return self._investment

        @property
        def borrowers_profile(self):
            return self._borrowers_profile


class InvestmentRejectPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, investment):
            assert isinstance(investment, pb.Investment), type(investment)

            super(Payload.Implementation, self).__init__(meta)
            self._investment = investment

        @property
        def investment(self):
            return self._investment


class CampaignBidPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, investment, campaign, loan_request, house, mortgage):
            assert isinstance(investment, pb.Investment), type(investment)
            assert isinstance(campaign, pb.Campaign), type(campaign)
            assert isinstance(loan_request, pb.LoanRequest), type(loan_request)
            assert isinstance(house, pb.House), type(house)
            assert isinstance(mortgage, pb.Mortgage), type(mortgage)

            super(Payload.Implementation, self).__init__(meta)
            self._investment = investment
            self._campaign = campaign
            self._loan_request = loan_request
            self._house = house
            self._mortgage = mortgage

        @property
        def investment(self):
            return self._investment

        @property
        def campaign(self):
            return self._campaign

        @property
        def loan_request(self):
            return self._loan_request

        @property
        def house(self):
            return self._house

        @property
        def mortgage(self):
            return self._mortgage


# class SignedConfirmPayload(Payload):
#     class Implementation(Payload.Implementation):
#         def __init__(self, meta, benefactor, beneficiary, agreement_benefactor, agreement_beneficiary,
#                      sequence_number_benefactor, sequence_number_beneficiary, previous_hash_benefactor,
#                      previous_hash_beneficiary, signature_benefactor, signature_beneficiary, insert_time):
#             assert isinstance(benefactor, str)
#             assert isinstance(beneficiary, str)
#             assert isinstance(agreement_benefactor, DatabaseModel)
#             if agreement_beneficiary:
#                 assert isinstance(agreement_beneficiary, DatabaseModel)
#             assert isinstance(sequence_number_benefactor, int)
#             assert isinstance(sequence_number_beneficiary, int)
#             assert isinstance(previous_hash_benefactor, str), "Previous has not a string, rather %s with type %s" % (
#             previous_hash_benefactor, type(previous_hash_benefactor))
#             assert isinstance(previous_hash_beneficiary, str)
#             assert isinstance(signature_benefactor, str)
#             assert isinstance(signature_beneficiary, str)
#             assert isinstance(insert_time, int)
#
#             super(SignedConfirmPayload.Implementation, self).__init__(meta)
#
#             self._benefactor = benefactor
#             self._beneficiary = beneficiary
#             self._agreement_benefactor = agreement_benefactor
#             self._agreement_beneficiary = agreement_beneficiary
#             self._sequence_number_benefactor = sequence_number_benefactor
#             self._sequence_number_beneficiary = sequence_number_beneficiary
#             self._previous_hash_benefactor = previous_hash_benefactor
#             self._previous_hash_beneficiary = previous_hash_beneficiary
#             self._signature_benefactor = signature_benefactor
#             self._signature_beneficiary = signature_beneficiary
#             self._insert_time = insert_time
#
#         @property
#         def benefactor(self):
#             return self._benefactor
#
#         @property
#         def beneficiary(self):
#             return self._beneficiary
#
#         @property
#         def agreement_benefactor(self):
#             return self._agreement_benefactor
#
#         @property
#         def agreement_beneficiary(self):
#             return self._agreement_beneficiary
#
#         @property
#         def sequence_number_benefactor(self):
#             return self._sequence_number_benefactor
#
#         @property
#         def sequence_number_beneficiary(self):
#             return self._sequence_number_beneficiary
#
#         @property
#         def previous_hash_benefactor(self):
#             return self._previous_hash_benefactor
#
#         @property
#         def previous_hash_beneficiary(self):
#             return self._previous_hash_beneficiary
#
#         @property
#         def signature_benefactor(self):
#             return self._signature_benefactor
#
#         @property
#         def signature_beneficiary(self):
#             return self._signature_beneficiary
#
#         @signature_benefactor.setter
#         def signature_benefactor(self, value):
#             self._signature_benefactor = value
#
#         @signature_beneficiary.setter
#         def signature_beneficiary(self, value):
#             self._signature_beneficiary = value
#
#         @property
#         def insert_time(self):
#             return self._insert_time


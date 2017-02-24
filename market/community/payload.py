from market.dispersy.payload import Payload, IntroductionRequestPayload, IntroductionResponsePayload

from market.models.user import User


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
















class SignedConfirmPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, benefactor, beneficiary, agreement_benefactor, agreement_beneficiary,
                     sequence_number_benefactor, sequence_number_beneficiary, previous_hash_benefactor,
                     previous_hash_beneficiary, signature_benefactor, signature_beneficiary, insert_time):
            assert isinstance(benefactor, str)
            assert isinstance(beneficiary, str)
            assert isinstance(agreement_benefactor, DatabaseModel)
            if agreement_beneficiary:
                assert isinstance(agreement_beneficiary, DatabaseModel)
            assert isinstance(sequence_number_benefactor, int)
            assert isinstance(sequence_number_beneficiary, int)
            assert isinstance(previous_hash_benefactor, str), "Previous has not a string, rather %s with type %s" % (
            previous_hash_benefactor, type(previous_hash_benefactor))
            assert isinstance(previous_hash_beneficiary, str)
            assert isinstance(signature_benefactor, str)
            assert isinstance(signature_beneficiary, str)
            assert isinstance(insert_time, int)

            super(SignedConfirmPayload.Implementation, self).__init__(meta)

            self._benefactor = benefactor
            self._beneficiary = beneficiary
            self._agreement_benefactor = agreement_benefactor
            self._agreement_beneficiary = agreement_beneficiary
            self._sequence_number_benefactor = sequence_number_benefactor
            self._sequence_number_beneficiary = sequence_number_beneficiary
            self._previous_hash_benefactor = previous_hash_benefactor
            self._previous_hash_beneficiary = previous_hash_beneficiary
            self._signature_benefactor = signature_benefactor
            self._signature_beneficiary = signature_beneficiary
            self._insert_time = insert_time

        @property
        def benefactor(self):
            return self._benefactor

        @property
        def beneficiary(self):
            return self._beneficiary

        @property
        def agreement_benefactor(self):
            return self._agreement_benefactor

        @property
        def agreement_beneficiary(self):
            return self._agreement_beneficiary

        @property
        def sequence_number_benefactor(self):
            return self._sequence_number_benefactor

        @property
        def sequence_number_beneficiary(self):
            return self._sequence_number_beneficiary

        @property
        def previous_hash_benefactor(self):
            return self._previous_hash_benefactor

        @property
        def previous_hash_beneficiary(self):
            return self._previous_hash_beneficiary

        @property
        def signature_benefactor(self):
            return self._signature_benefactor

        @property
        def signature_beneficiary(self):
            return self._signature_beneficiary

        @signature_benefactor.setter
        def signature_benefactor(self, value):
            self._signature_benefactor = value

        @signature_beneficiary.setter
        def signature_beneficiary(self, value):
            self._signature_beneficiary = value

        @property
        def insert_time(self):
            return self._insert_time


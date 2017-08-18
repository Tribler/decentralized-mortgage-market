from dispersy.payload import Payload, IntroductionRequestPayload


class MoneyIntroPayload(IntroductionRequestPayload):

    class Implementation(IntroductionRequestPayload.Implementation):

        def __init__(self, meta, destination_address, source_lan_address, source_wan_address, advice, connection_type, sync, identifier, services_map=None):
            IntroductionRequestPayload.Implementation.__init__(self, meta, destination_address, source_lan_address, source_wan_address, advice, connection_type, sync, identifier)

            self._services_map = services_map or {}

        def set_services_map(self, services_map):
            self._services_map = services_map

        @property
        def services_map(self):
            return self._services_map


class ServicesInfoPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, services_map):
            assert isinstance(services_map, dict), type(services_map)
            super(ServicesInfoPayload.Implementation, self).__init__(meta)
            self._services_map = services_map

        @property
        def services_map(self):
            return self._services_map


class CapacityQueryPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, identifier, bank_id):
            assert isinstance(identifier, int), type(identifier)
            assert isinstance(bank_id, str), type(bank_id)
            super(CapacityQueryPayload.Implementation, self).__init__(meta)
            self._identifier = identifier
            self._bank_id = bank_id

        @property
        def identifier(self):
            return self._identifier

        @property
        def bank_id(self):
            return self._bank_id


class CapacityResponsePayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, identifier, bank_id, capacity):
            assert isinstance(identifier, int), type(identifier)
            assert isinstance(bank_id, str), type(bank_id)
            assert isinstance(capacity, float), type(capacity)
            super(CapacityResponsePayload.Implementation, self).__init__(meta)
            self._identifier = identifier
            self._bank_id = bank_id
            self._capacity = capacity

        @property
        def identifier(self):
            return self._identifier

        @property
        def bank_id(self):
            return self._bank_id

        @property
        def capacity(self):
            return self._capacity


class PaymentToSwitchPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, identifier, to_switch_txid, from_switch_txid, from_iban,
                     to_iban, final_destination_iban, amount):
            assert isinstance(identifier, int), type(identifier)
            assert isinstance(to_switch_txid, str), type(to_switch_txid)
            assert isinstance(from_switch_txid, str), type(from_switch_txid)
            assert isinstance(from_iban, str), type(from_iban)
            assert isinstance(to_iban, str), type(to_iban)
            assert isinstance(final_destination_iban, str), type(final_destination_iban)
            assert isinstance(amount, float), type(amount)
            super(PaymentToSwitchPayload.Implementation, self).__init__(meta)
            self._identifier = identifier
            self._to_switch_txid = to_switch_txid
            self._from_switch_txid = from_switch_txid
            self._from_iban = from_iban
            self._to_iban = to_iban
            self._final_destination_iban = final_destination_iban
            self._amount = amount

        @property
        def identifier(self):
            return self._identifier

        @property
        def to_switch_txid(self):
            return self._to_switch_txid

        @property
        def from_switch_txid(self):
            return self._from_switch_txid

        @property
        def from_iban(self):
            return self._from_iban

        @property
        def to_iban(self):
            return self._to_iban

        @property
        def final_destination_iban(self):
            return self._final_destination_iban

        @property
        def amount(self):
            return self._amount


class PaymentFromSwitchPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, identifier):
            assert isinstance(identifier, int), type(identifier)
            super(PaymentFromSwitchPayload.Implementation, self).__init__(meta)
            self._identifier = identifier

        @property
        def identifier(self):
            return self._identifier

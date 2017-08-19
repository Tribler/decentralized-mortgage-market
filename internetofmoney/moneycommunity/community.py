import logging

import time
from random import shuffle

from twisted.internet.defer import succeed, Deferred
from twisted.internet.task import LoopingCall

from internetofmoney.moneycommunity import generate_txid
from internetofmoney.moneycommunity.conversion import MoneyConversion
from internetofmoney.moneycommunity.payload import MoneyIntroPayload, CapacityQueryPayload, CapacityResponsePayload, \
    PaymentToSwitchPayload, PaymentFromSwitchPayload, ServicesInfoPayload
from internetofmoney.utils.iban import IBANUtil
from dispersy.authentication import MemberAuthentication
from dispersy.candidate import WalkCandidate
from dispersy.community import Community
from dispersy.conversion import DefaultConversion
from dispersy.destination import CandidateDestination
from dispersy.distribution import DirectDistribution
from dispersy.message import Message, DelayMessageByProof, DropMessage
from dispersy.requestcache import IntroductionRequestCache, RandomNumberCache
from dispersy.resolution import PublicResolution

logger = logging.getLogger(__name__)


class CapacityRequestCache(RandomNumberCache):
    """
    This cache keeps track of outstanding capacity request messages. It contains information about the candidates
    that we should query.
    """

    def __init__(self, community, eligable_candidates, required_capacity, query_deferred):
        super(CapacityRequestCache, self).__init__(community.request_cache, u"capacity")
        self.community = community
        self.eligable_candidates = eligable_candidates
        self.required_capacity = required_capacity
        self.query_deferred = query_deferred

    def on_timeout(self):
        pass

    def pop_next_candidate(self):
        del self.eligable_candidates[0]
        return self.eligable_candidates[0]


class SwitchPaymentRequestCache(RandomNumberCache):
    """
    This cache keeps track of payments to the switches.
    """
    def __init__(self, community, from_iban, to_iban, to_switch_txid, from_switch_txid, amount, payment_deferred):
        super(SwitchPaymentRequestCache, self).__init__(community.request_cache, u"switch-payment")
        self.from_iban = from_iban
        self.to_iban = to_iban
        self.to_switch_txid = to_switch_txid
        self.from_switch_txid = from_switch_txid
        self.payment_deferred = payment_deferred
        self.amount = amount

    def on_timeout(self):
        pass


class MoneyCommunity(Community):

    @classmethod
    def get_master_members(cls, dispersy):
        master_key = "3081a7301006072a8648ce3d020106052b81040027038192000405f097ba61240b9ed194456b89e13e80de96526" \
                     "ecccb334736b95c9de488f4eff4579dacdfae2698a23b044269738cd33f29086de65be3a2ff23899670125536b9" \
                     "004fda9eeb4029014cbc0e257b471014b77c959be333c85ba87d4973ba4f4710e19ebf8435a589a099e907bf52e" \
                     "7b3bfeed3ceee38cb6691966a7a863ffb07f708d650be54a8cf3c70e127c614256d".decode("HEX")
        master = dispersy.get_member(public_key=master_key)
        return [master]

    def initialize(self, money_chain_community=None):
        super(MoneyCommunity, self).initialize()

        self.bank_managers = {}
        self.candidate_services_map = {}
        self.money_chain_community = money_chain_community

        logger.info("Money community initialized")

    def start_walking(self):
        self.register_task("take step", LoopingCall(self.take_step)).start(5.0, now=False)

    def initiate_meta_messages(self):
        return super(MoneyCommunity, self).initiate_meta_messages() + [
            Message(self, u"services-info",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    ServicesInfoPayload(),
                    self.check_message,
                    self.on_services_info),
            Message(self, u"capacity-query",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    CapacityQueryPayload(),
                    self.check_capacity_query,
                    self.on_capacity_query),
            Message(self, u"capacity-response",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    CapacityResponsePayload(),
                    self.check_message,
                    self.on_capacity_response),
            Message(self, u"payment-to-switch",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    PaymentToSwitchPayload(),
                    self.check_payment_to_switch_message,
                    self.on_payment_to_switch_message),
            Message(self, u"payment-from-switch",
                    MemberAuthentication(),
                    PublicResolution(),
                    DirectDistribution(),
                    CandidateDestination(),
                    PaymentFromSwitchPayload(),
                    self.check_message,
                    self.on_payment_from_switch_message),
        ]

    def _initialize_meta_messages(self):
        super(MoneyCommunity, self)._initialize_meta_messages()

        ori = self._meta_messages[u"dispersy-introduction-request"]
        new = Message(self, ori.name, ori.authentication, ori.resolution,
                      ori.distribution, ori.destination, MoneyIntroPayload(), ori.check_callback, ori.handle_callback)
        self._meta_messages[u"dispersy-introduction-request"] = new

    def initiate_conversions(self):
        return [DefaultConversion(self), MoneyConversion(self)]

    def check_message(self, messages):
        for message in messages:
            allowed, _ = self._timeline.check(message)
            if allowed:
                yield message
            else:
                yield DelayMessageByProof(message)

    def on_introduction_request(self, messages):
        super(MoneyCommunity, self).on_introduction_request(messages)

        for message in messages:
            if message.payload.services_map:
                self.parse_services_map(message.candidate, message.payload.services_map)
                self.send_services_info(message.candidate)

    def parse_services_map(self, candidate, services_map):
        """
        Parse an incoming list of services
        """
        candidate_services_map = {}
        for bank_id, iban in services_map.iteritems():
            if IBANUtil.is_valid_iban(iban):
                candidate_services_map[bank_id] = iban

        self.candidate_services_map[candidate] = candidate_services_map

    def create_services_map(self):
        """
        Create a list of services that this node can offer.
        """
        services_map = {}
        for manager in self.bank_managers.itervalues():
            if manager.is_switch_capable() and manager.registered_account()\
                    and IBANUtil.is_valid_iban(manager.get_address()):
                services_map[IBANUtil.get_bank_id(manager.get_address())] = manager.get_address()

        return services_map

    def create_introduction_request(self, destination, allow_sync):
        assert isinstance(destination, WalkCandidate), [type(destination), destination]

        cache = self._request_cache.add(IntroductionRequestCache(self, destination))
        payload = (destination.sock_addr, self._dispersy._lan_address, self._dispersy._wan_address, True,
                   self._dispersy._connection_type, None, cache.number, self.create_services_map())

        destination.walk(time.time())
        self.add_candidate(destination)

        meta_request = self.get_meta_message(u"dispersy-introduction-request")
        request = meta_request.impl(authentication=(self.my_member,),
                                    distribution=(self.global_time,),
                                    destination=(destination,),
                                    payload=payload)

        self._logger.debug(u"%s %s sending introduction request to %s", self.cid.encode("HEX"), type(self), destination)

        self._dispersy._forward([request])
        return request

    def has_eligable_router(self, from_bank, to_bank, amount):
        """
        Returns a deferred that fires with a eligable router if there's one. Else, the deferred fires with None.
        This method first searches for a known router. If there isn't any, return immediately.
        If there are eligable routers, it sends a capacity query to each of these routers and wait for a response.
        Next, we check whether these capacities are enough to transfer the amount of money we want and we select
        one of the routers randomly.
        """
        query_deferred = Deferred()

        eligable_candidates = []
        for candidate, services_map in self.candidate_services_map.iteritems():
            if from_bank in services_map.keys() and to_bank in services_map:
                eligable_candidates.append((candidate, services_map[from_bank]))

        if not eligable_candidates:
            return succeed(None)

        shuffle(eligable_candidates)
        cache = self.request_cache.add(CapacityRequestCache(self, eligable_candidates, amount, query_deferred))

        # Send a capacity-query to the first candidate
        self.send_capacity_query(eligable_candidates[0][0], cache.number, to_bank)

        return query_deferred

    def send_money_using_router(self, router_candidate, source_manager, amount, destination_iban, final_destination_iban):
        """
        Send some money using a specific money router.
        """
        to_switch_txid = generate_txid()  # This is the ID of the transaction between the sender and the switch
        from_switch_txid = generate_txid()  # This is the ID of the transaction between the switch and the final receiver
        switch_deferred = Deferred()

        def on_switch_payment_done(_):
            from_iban = source_manager.get_address()
            cache = self.request_cache.add(SwitchPaymentRequestCache(self, from_iban, destination_iban, to_switch_txid,
                                                                     from_switch_txid, amount, switch_deferred))

            # Now we send a message to the router candidate that we have transferred the money.
            meta = self.get_meta_message(u"payment-to-switch")
            message = meta.impl(
                authentication=(self.my_member,),
                distribution=(self.claim_global_time(),),
                destination=(router_candidate,),
                payload=(cache.number, to_switch_txid, from_switch_txid, from_iban,
                         destination_iban, final_destination_iban, float(amount))
            )

            self.dispersy.store_update_forward([message], True, False, True)

        source_manager.perform_payment(amount, destination_iban, to_switch_txid).addCallback(on_switch_payment_done)
        return switch_deferred

    def on_services_info(self, messages):
        for message in messages:
            self.parse_services_map(message.candidate, message.payload.services_map)

    def send_services_info(self, candidate):
        meta = self.get_meta_message(u"services-info")
        message = meta.impl(
            authentication=(self.my_member,),
            distribution=(self.claim_global_time(),),
            destination=(candidate,),
            payload=(self.create_services_map(),)
        )

        self._logger.debug(u"%s %s sending services-info to %s", self.cid.encode("HEX"), type(self), candidate)
        self.dispersy.store_update_forward([message], True, False, True)

    def check_capacity_query(self, messages):
        for message in messages:
            query_bank_id = message.payload.bank_id
            if query_bank_id not in self.bank_managers.keys():
                yield DropMessage(message, "Invalid bank id (%s)" % query_bank_id)
            else:
                yield message

    def send_capacity_query(self, candidate, identifier, bank_id):
        meta = self.get_meta_message(u"capacity-query")
        message = meta.impl(
            authentication=(self.my_member,),
            distribution=(self.claim_global_time(),),
            destination=(candidate,),
            payload=(identifier, bank_id,)
        )

        self.dispersy.store_update_forward([message], True, False, True)

    def on_capacity_query(self, messages):
        for message in messages:
            manager = self.bank_managers[message.payload.bank_id]
            manager.get_balance().addCallback(
                lambda balance: self.send_capacity_response(
                    message.candidate, message.payload.identifier, message.payload.bank_id, balance["available"]))

    def send_capacity_response(self, candidate, identifier, bank_id, capacity):
        meta = self.get_meta_message(u"capacity-response")
        message = meta.impl(
            authentication=(self.my_member,),
            distribution=(self.claim_global_time(),),
            destination=(candidate,),
            payload=(identifier, bank_id, float(capacity))
        )

        self.dispersy.store_update_forward([message], True, False, True)

    def on_capacity_response(self, messages):
        for message in messages:
            request = self.request_cache.get(u"capacity", message.payload.identifier)  # TODO Drop message if identifier/bank is not known
            if message.payload.capacity >= request.required_capacity:  # We found an eligable candidate
                self.request_cache.pop(u"capacity", message.payload.identifier)
                request.query_deferred.callback(message.candidate)
            elif len(request.eligable_candidates) == 1:  # No candidates left
                request.query_deferred.callback(None)
            else:  # Just query the next candidate
                self.send_capacity_query(request.pop_next_candidate(),
                                         message.payload.identifier, message.payload.bank_id)

    def check_payment_to_switch_message(self, messages):
        for message in messages:
            receive_iban = message.payload.to_iban
            from_iban = message.payload.from_iban
            final_destination_iban = message.payload.final_destination_iban

            if not IBANUtil.is_valid_iban(receive_iban):
                yield DropMessage(message, "Invalid receive IBAN (%s)" % receive_iban)
                continue

            if not IBANUtil.is_valid_iban(from_iban):
                yield DropMessage(message, "Invalid source IBAN (%s)" % from_iban)
                continue

            if not IBANUtil.is_valid_iban(final_destination_iban):
                yield DropMessage(message, "Invalid destination IBAN (%s)" % final_destination_iban)
                continue

            if IBANUtil.get_bank_id(receive_iban) not in self.bank_managers.keys():
                yield DropMessage(message, "No associated bank manager for IBAN %s found" % receive_iban)
                continue

            required_manager = self.bank_managers[IBANUtil.get_bank_id(receive_iban)]
            if not required_manager.registered_account():
                yield DropMessage(message, "Bank manager has no registered account for IBAN %s" % receive_iban)
                continue

            if required_manager.get_address() != receive_iban:
                yield DropMessage(message, "IBAN of manager does not match received IBAN (%s != %s)" %
                                  (required_manager.get_address(), receive_iban))
                continue

            yield message

    def on_payment_to_switch_message(self, messages):
        for message in messages:
            # We received a payment, transfer the money to the final destination if we received this payment
            receive_iban = message.payload.to_iban
            required_manager = self.bank_managers[IBANUtil.get_bank_id(receive_iban)]

            def on_performed_payment(_):
                # Send a message back that we have transferred the money to the final destination
                # TODO Mitchell: recharge trigger here? Maybe this requires to keep track of what we have transferred between our own bank accounts?

                meta = self.get_meta_message(u"payment-from-switch")
                new_message = meta.impl(
                    authentication=(self.my_member,),
                    distribution=(self.claim_global_time(),),
                    destination=(message.candidate,),
                    payload=(message.payload.identifier,)
                )

                self.dispersy.store_update_forward([new_message], True, False, True)

            def on_received_payment(transaction):
                # We have received the money on the switch, record it on the blockchain
                if self.money_chain_community:
                    chain_transaction = {'from': message.payload.from_iban, 'to': message.payload.to_iban,
                                         'amount': message.payload.amount, 'type': 'switch_incoming'}
                    self.money_chain_community.sign_block(message.candidate, message.candidate.get_member().public_key,
                                                          chain_transaction)

                # Now we transfer it to the final destination
                to_iban = message.payload.final_destination_iban
                transfer_manager = self.bank_managers[IBANUtil.get_bank_id(to_iban)]
                transfer_manager.perform_payment(
                    transaction["amount"], message.payload.final_destination_iban, message.payload.from_switch_txid)\
                    .addCallback(on_performed_payment)

            required_manager.monitor_transactions(message.payload.to_switch_txid).addCallback(on_received_payment)

    def on_payment_from_switch_message(self, messages):
        for message in messages:
            # The switch has transferred the money to the final destination IBAN.
            request = self.request_cache.pop(u"switch-payment", message.payload.identifier)
            request.payment_deferred.callback(message)

            # We acknowledge the outgoing transaction of the switch by signing a block again
            if self.money_chain_community:
                chain_transaction = {'from': request.from_iban, 'to': request.to_iban,
                                     'amount': request.amount, 'type': 'switch_outgoing'}
                self.money_chain_community.sign_block(message.candidate, message.candidate.get_member().public_key,
                                                      chain_transaction)

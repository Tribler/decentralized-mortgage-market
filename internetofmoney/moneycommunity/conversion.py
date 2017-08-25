from dispersy.conversion import BinaryConversion
from dispersy.message import DropPacket
from internetofmoney.utils.encoding import encode, decode


class MoneyConversion(BinaryConversion):

    def __init__(self, community):
        super(MoneyConversion, self).__init__(community, "\x01")
        self.define_meta_message(chr(1), community.get_meta_message(u"services-info"),
                                 self._encode_services_info, self._decode_services_info)
        self.define_meta_message(chr(2), community.get_meta_message(u"capacity-query"),
                                 self._encode_capacity_query, self._decode_capacity_query)
        self.define_meta_message(chr(3), community.get_meta_message(u"capacity-response"),
                                 self._encode_capacity_response, self._decode_capacity_response)
        self.define_meta_message(chr(4), community.get_meta_message(u"payment-to-switch"),
                                 self._encode_payment_to_switch, self._decode_payment_to_switch)
        self.define_meta_message(chr(5), community.get_meta_message(u"payment-from-switch"),
                                 self._encode_payment_from_switch, self._decode_payment_from_switch)

    def _encode_introduction_request(self, message):
        data = BinaryConversion._encode_introduction_request(self, message)
        data.extend(encode(message.payload.services_map))
        return data

    def _decode_introduction_request(self, placeholder, offset, data):
        offset, payload = BinaryConversion._decode_introduction_request(self, placeholder, offset, data)

        if len(data) > offset:
            offset, services_map = decode(data, offset)
            payload.set_services_map(services_map)

        return offset, payload

    def _decode_payload(self, placeholder, offset, data, types):
        try:
            offset, payload = decode(data, offset)
        except ValueError:
            raise DropPacket("Unable to decode the payload")

        if not isinstance(payload, tuple):
            raise DropPacket("Invalid payload type")

        args = []
        cur_ind = 0
        for arg_type in types:
            try:
                if arg_type == str or arg_type == int:
                    args.append(payload[cur_ind])
                    cur_ind += 1
                else:
                    args.append(arg_type(payload[cur_ind]))
                    cur_ind += 1
            except ValueError:
                raise DropPacket("Invalid '" + arg_type.__name__ + "' type")
        return offset, placeholder.meta.payload.implement(*args)

    def _encode_services_info(self, message):
        packet = encode((message.payload.services_map,))
        return packet,

    def _decode_services_info(self, placeholder, offset, data):
        return self._decode_payload(placeholder, offset, data, [dict])

    def _encode_capacity_query(self, message):
        packet = encode((message.payload.identifier, message.payload.bank_id,))
        return packet,

    def _decode_capacity_query(self, placeholder, offset, data):
        return self._decode_payload(placeholder, offset, data, [int, str])

    def _encode_capacity_response(self, message):
        packet = encode((message.payload.identifier, message.payload.bank_id, message.payload.capacity))
        return packet,

    def _decode_capacity_response(self, placeholder, offset, data):
        return self._decode_payload(placeholder, offset, data, [int, str, float])

    def _encode_payment_to_switch(self, message):
        packet = encode((message.payload.identifier, message.payload.to_switch_txid, message.payload.from_switch_txid,
                         message.payload.from_iban, message.payload.to_iban, message.payload.final_destination_iban,
                         message.payload.amount))
        return packet,

    def _decode_payment_to_switch(self, placeholder, offset, data):
        return self._decode_payload(placeholder, offset, data, [int, str, str, str, str, str, float])

    def _encode_payment_from_switch(self, message):
        packet = encode((message.payload.identifier,))
        return packet,

    def _decode_payment_from_switch(self, placeholder, offset, data):
        return self._decode_payload(placeholder, offset, data, [int])

from market.community.blockchain import conversion_pb2

from market.dispersy.conversion import BinaryConversion
from protobuf_to_dict import dict_to_protobuf, protobuf_to_dict


class BlockchainConversion(BinaryConversion):

    def __init__(self, community):
        super(BlockchainConversion, self).__init__(community, "\x02")

        msg_types = {u'signature-request': (chr(1), conversion_pb2.SignatureRequestMessage),
                     u'signature-response': (chr(2), conversion_pb2.SignatureResponseMessage),
                     u'contract': (chr(3), conversion_pb2.ContractMessage),
                     u'block-request': (chr(4), conversion_pb2.BlockRequestMessage),
                     u'block': (chr(5), conversion_pb2.BlockMessage)}

        for name, (byte, proto) in msg_types.iteritems():
            self.define_meta_message(byte,
                                     community.get_meta_message(name),
                                     lambda msg, proto=proto: self._encode_protobuf(proto, msg),
                                     lambda placeholder, offset, data, proto=proto:
                                            self._decode_protobuf(proto, placeholder, offset, data))

    def _encode_protobuf(self, message_cls, message):
        return dict_to_protobuf(message_cls, message.payload.dictionary).SerializeToString(),

    def _decode_protobuf(self, message_cls, placeholder, offset, data):
        msg = message_cls()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(protobuf_to_dict(msg))

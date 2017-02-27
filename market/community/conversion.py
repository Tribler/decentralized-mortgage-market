import mortgage_pb2 as pb

from struct import pack, unpack_from

from market.dispersy.conversion import BinaryConversion
from protobuf_to_dict import dict_to_protobuf, protobuf_to_dict


class MortgageConversion(BinaryConversion):

    def __init__(self, community):
        super(MortgageConversion, self).__init__(community, "\x02")

        self.define_meta_message(chr(1),
                                 community.get_meta_message(u"user-request"),
                                 lambda msg: self._encode_protobuf(pb.UserRequestMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.UserRequestMessage, *args))
        self.define_meta_message(chr(2),
                                 community.get_meta_message(u"user-response"),
                                 lambda msg: self._encode_protobuf(pb.UserResponseMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.UserResponseMessage, *args))
        self.define_meta_message(chr(3),
                                 community.get_meta_message(u"loan-request"),
                                 lambda msg: self._encode_protobuf(pb.LoanRequestMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.LoanRequestMessage, *args))
        self.define_meta_message(chr(4),
                                 community.get_meta_message(u"loan-reject"),
                                 lambda msg: self._encode_protobuf(pb.LoanRejectMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.LoanRejectMessage, *args))
        self.define_meta_message(chr(5),
                                 community.get_meta_message(u"mortgage-offer"),
                                 lambda msg: self._encode_protobuf(pb.MortgageOfferMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.MortgageOfferMessage, *args))
        self.define_meta_message(chr(6),
                                 community.get_meta_message(u"mortgage-accept"),
                                 lambda msg: self._encode_protobuf(pb.MortgageAcceptMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.MortgageAcceptMessage, *args))
        self.define_meta_message(chr(7),
                                 community.get_meta_message(u"mortgage-reject"),
                                 lambda msg: self._encode_protobuf(pb.MortgageRejectMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.MortgageRejectMessage, *args))
        self.define_meta_message(chr(8),
                                 community.get_meta_message(u"investment-offer"),
                                 lambda msg: self._encode_protobuf(pb.InvestmentOfferMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.InvestmentOfferMessage, *args))
        self.define_meta_message(chr(9),
                                 community.get_meta_message(u"investment-accept"),
                                 lambda msg: self._encode_protobuf(pb.InvestmentAcceptMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.InvestmentAcceptMessage, *args))
        self.define_meta_message(chr(10),
                                 community.get_meta_message(u"investment-reject"),
                                 lambda msg: self._encode_protobuf(pb.InvestmentRejectMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.InvestmentRejectMessage, *args))
        self.define_meta_message(chr(11),
                                 community.get_meta_message(u"campaign-bid"),
                                 lambda msg: self._encode_protobuf(pb.CampaignBidMessage, msg),
                                 lambda *args: self._decode_protobuf(pb.CampaignBidMessage, *args))
#         self.define_meta_message(chr(10),
#                                  community.get_meta_message(u"signed-confirm"),
#                                  self._encode_signed_confirm,
#                                  self._decode_signed_confirm)

    def _encode_protobuf(self, message_cls, message):
        return dict_to_protobuf(message_cls, message.payload.dictionary).SerializeToString(),

    def _decode_protobuf(self, message_cls, placeholder, offset, data):
        msg = message_cls()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(protobuf_to_dict(msg))












#     def _encode_signed_confirm(self, message):
#         packet = encode(
#                 (
#                     message.payload.benefactor,
#                     message.payload.beneficiary,
#                     message.payload.agreement_benefactor.encode(),
#                     message.payload.agreement_beneficiary and message.payload.agreement_beneficiary.encode() or "",
#                     message.payload.sequence_number_benefactor,
#                     message.payload.sequence_number_beneficiary,
#                     message.payload.previous_hash_benefactor,
#                     message.payload.previous_hash_beneficiary,
#                     message.payload.signature_benefactor,
#                     message.payload.signature_beneficiary,
#                     message.payload.insert_time
#                  )
#                 )
#         return packet,
#
#
#     def _decode_signed_confirm(self, placeholder, offset, data):
#         try:
#             offset, payload = decode(data, offset)
#         except ValueError:
#             raise DropPacket("Unable to decode the SignedConfirm-payload")
#
#         if not isinstance(payload, tuple):
#             raise DropPacket("Invalid payload type")
#
#         # benefactor, 0
#         # beneficiary, 1
#         # agreement_benefactor_encoded, 2
#         # agreement_beneficiary_encoded, 3
#         # sequence_number_benefactor, 4
#         # sequence_number_beneficiary, 5
#         # previous_hash_benefactor, 6
#         # previous_hash_beneficiary, 7
#         # signature_benefactor, 8
#         # signature_beneficiary, 9
#         # insert_time 10
#
#         if not isinstance(payload[0], str):
#             raise DropPacket("Invalid 'benefactor' type")
#         if not isinstance(payload[1], str):
#             raise DropPacket("Invalid 'beneficiary' type")
#         # TODO: Do the rest.
#
#         agreement_benefactor = DatabaseModel.decode(payload[2])
#         agreement_beneficiary = DatabaseModel.decode(payload[3])
#
#         return offset, placeholder.meta.payload.implement(
#             payload[0],
#             payload[1],
#             agreement_benefactor,
#             agreement_beneficiary,
#             payload[4],
#             payload[5],
#             payload[6],
#             payload[7],
#             payload[8],
#             payload[9],
#             payload[10],
#         )
#
#
#     def _encode_model(self, message):
#         encoded_models = dict()
#
#         for field in message.payload.fields:
#             encoded_models[field] = message.payload.models[field].encode()
#
#         packet = encode((message.payload.fields, encoded_models))
#         return packet,
#
#
#     def _decode_model(self, placeholder, offset, data):
#         try:
#             offset, payload = decode(data, offset)
#         except ValueError:
#             raise DropPacket("Unable to decode the model payload")
#
#         if not isinstance(payload, tuple):
#             raise DropPacket("Invalid payload type")
#
#         fields, encoded_models = payload
#         if not isinstance(fields, list):
#             raise DropPacket("Invalid 'fields' type")
#         if not isinstance(encoded_models, dict):
#             raise DropPacket("Invalid 'models' type")
#
#         decoded_models = dict()
#         for field in fields:
#             decoded_models[field] = DatabaseModel.decode(encoded_models[field])
#
#         return offset, placeholder.meta.payload.implement(fields, decoded_models)

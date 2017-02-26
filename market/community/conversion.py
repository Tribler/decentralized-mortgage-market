import mortgage_pb2 as pb

from struct import pack, unpack_from

from market.dispersy.conversion import BinaryConversion


class MortgageConversion(BinaryConversion):

    def __init__(self, community):
        super(MortgageConversion, self).__init__(community, "\x02")

        self.define_meta_message(chr(1),
                                 community.get_meta_message(u"loan-request"),
                                 self._encode_loan_request,
                                 self._decode_loan_request)
        self.define_meta_message(chr(2),
                                 community.get_meta_message(u"loan-reject"),
                                 self._encode_loan_reject,
                                 self._decode_loan_reject)
        self.define_meta_message(chr(3),
                                 community.get_meta_message(u"mortgage-offer"),
                                 self._encode_mortgage_offer,
                                 self._decode_mortgage_offer)
        self.define_meta_message(chr(4),
                                 community.get_meta_message(u"mortgage-accept"),
                                 self._encode_mortgage_accept,
                                 self._decode_mortgage_accept)
        self.define_meta_message(chr(5),
                                 community.get_meta_message(u"mortgage-reject"),
                                 self._encode_mortgage_reject,
                                 self._decode_mortgage_reject)
        self.define_meta_message(chr(6),
                                 community.get_meta_message(u"investment-offer"),
                                 self._encode_investment_offer,
                                 self._decode_investment_offer)
        self.define_meta_message(chr(7),
                                 community.get_meta_message(u"investment-accept"),
                                 self._encode_investment_accept,
                                 self._decode_investment_accept)
        self.define_meta_message(chr(8),
                                 community.get_meta_message(u"investment-reject"),
                                 self._encode_investment_reject,
                                 self._decode_investment_reject)
        self.define_meta_message(chr(9),
                                 community.get_meta_message(u"campaign-bid"),
                                 self._encode_campaign_bid,
                                 self._decode_campaign_bid)
#         self.define_meta_message(chr(10),
#                                  community.get_meta_message(u"signed-confirm"),
#                                  self._encode_signed_confirm,
#                                  self._decode_signed_confirm)

    def _encode_introduction_request(self, message):
        user_str = pb.IntroductionRequestMessage(user=message.payload.user).SerializeToString()
        data = [pack("!I", len(user_str),), user_str]
        data += list(super(MortgageConversion, self)._encode_introduction_request(message))
        return tuple(data)

    def _decode_introduction_request(self, placeholder, offset, data):
        user_len, = unpack_from('!I', data, offset)
        offset += 4
        user_str = data[offset:offset + user_len]
        offset += user_len
        offset, payload = super(MortgageConversion, self)._decode_introduction_request(placeholder, offset, data)
        msg = pb.IntroductionRequestMessage()
        msg.ParseFromString(user_str)
        payload._user = msg.user
        return (offset, payload)

    def _encode_introduction_response(self, message):
        user_str = pb.IntroductionResponseMessage(user=message.payload.user).SerializeToString()
        data = [pack("!I", len(user_str),), user_str]
        data += list(super(MortgageConversion, self)._encode_introduction_response(message))
        return tuple(data)

    def _decode_introduction_response(self, placeholder, offset, data):
        user_len, = unpack_from('!I', data, offset)
        offset += 4
        user_str = data[offset:offset + user_len]
        offset += user_len
        offset, payload = super(MortgageConversion, self)._decode_introduction_response(placeholder, offset, data)
        msg = pb.IntroductionResponseMessage()
        msg.ParseFromString(user_str)
        payload._user = msg.user
        return (offset, payload)

    def _encode_loan_request(self, message):
        payload = message.payload
        return pb.LoanRequestMessage(investment=payload.investment,
                                     campaign=payload.campaign,
                                     loan_request=payload.loan_request,
                                     house=payload.house,
                                     borrowers_profile=payload.borrower_profile).SerializeToString(),


    def _decode_loan_request(self, placeholder, offset, data):
        msg = pb.LoanRequestMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.investment,
                                                             msg.campaign,
                                                             msg.loan_request,
                                                             msg.house,
                                                             msg.borrowers_profile)

    def _encode_loan_reject(self, message):
        payload = message.payload
        return pb.LoanRejectMessage(loan_request=payload.loan_request).SerializeToString(),

    def _decode_loan_reject(self, placeholder, offset, data):
        msg = pb.LoanRejectMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.loan_request)

    def _encode_mortgage_offer(self, message):
        payload = message.payload
        return pb.MortgageOfferMessage(loan_request=payload.loan_request,
                                       mortgage=payload.mortgage).SerializeToString(),

    def _decode_mortgage_offer(self, placeholder, offset, data):
        msg = pb.MortgageOfferMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.loan_request,
                                                             msg.mortgage)

    def _encode_mortgage_accept(self, message):
        payload = message.payload
        return pb.MortgageAcceptMessage(investment=payload.investment,
                                     campaign=payload.campaign,
                                     loan_request=payload.loan_request,
                                     house=payload.house,
                                     borrowers_profile=payload.borrower_profile).SerializeToString(),

    def _decode_mortgage_accept(self, placeholder, offset, data):
        msg = pb.MortgageAcceptMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.campaign,
                                                             msg.mortgage)

    def _encode_mortgage_reject(self, message):
        payload = message.payload
        return pb.MortgageRejectMessage(investment=payload.investment,
                                     campaign=payload.campaign,
                                     loan_request=payload.loan_request,
                                     house=payload.house,
                                     borrowers_profile=payload.borrower_profile).SerializeToString(),

    def _decode_mortgage_reject(self, placeholder, offset, data):
        msg = pb.MortgageRejectMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.mortgage)

    def _encode_investment_offer(self, message):
        payload = message.payload
        return pb.InvestmentOfferMessage(investment=payload.investment,
                                     campaign=payload.campaign,
                                     loan_request=payload.loan_request,
                                     house=payload.house,
                                     borrowers_profile=payload.borrower_profile).SerializeToString(),

    def _decode_investment_offer(self, placeholder, offset, data):
        msg = pb.InvestmentOfferMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.investment,
                                                             msg.ivestor_profile)

    def _encode_investment_accept(self, message):
        payload = message.payload
        return pb.InvestmentAcceptMessage(investment=payload.investment,
                                     campaign=payload.campaign,
                                     loan_request=payload.loan_request,
                                     house=payload.house,
                                     borrowers_profile=payload.borrower_profile).SerializeToString(),

    def _decode_investment_accept(self, placeholder, offset, data):
        msg = pb.InvestmentAcceptMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.investment,
                                                             msg.borrowers_profile)

    def _encode_investment_reject(self, message):
        payload = message.payload
        return pb.InvestmentRejectMessage(investment=payload.investment,
                                     campaign=payload.campaign,
                                     loan_request=payload.loan_request,
                                     house=payload.house,
                                     borrowers_profile=payload.borrower_profile).SerializeToString(),

    def _decode_investment_reject(self, placeholder, offset, data):
        msg = pb.InvestmentRejectMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.investment)

    def _encode_campaign_bid(self, message):
        payload = message.payload
        return pb.CampaignBidMessage(investment=payload.investment,
                                     campaign=payload.campaign,
                                     loan_request=payload.loan_request,
                                     house=payload.house,
                                     borrowers_profile=payload.borrower_profile).SerializeToString(),

    def _decode_campaign_bid(self, placeholder, offset, data):
        msg = pb.CampaignBidMessage()
        msg.ParseFromString(data[offset:])
        return len(data), placeholder.meta.payload.implement(msg.investment,
                                                             msg.campaign,
                                                             msg.loan_request,
                                                             msg.house,
                                                             msg.mortgage)

















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

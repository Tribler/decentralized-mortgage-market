import base64
import json

from twisted.web import http, resource

from market.models.profile import InvestorProfile, BorrowersProfile
from market.restapi import get_param


class UsersEndpoint(resource.Resource):
    """
    This class handles requests regarding users in the mortgage market community.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

        self.putChild("profile", YouProfileEndpoint(market_community))

    def render_GET(self, request):
        return json.dumps({"you": self.market_community.data_manager.you.to_dictionary()})


class YouProfileEndpoint(resource.Resource):
    """
    This class handles requests regarding your profile.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        you = self.market_community.data_manager.you
        if not you.profile:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "you do not have a profile"})

        return json.dumps({"profile": you.profile.to_dictionary()})

    def render_PUT(self, request):
        parameters = http.parse_qs(request.content.read(), 1)
        if not get_param(parameters, 'role'):
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing role parameter"})

        role = get_param(parameters, 'role')
        required_fields = ['first_name', 'last_name', 'email', 'iban', 'phone_number']
        if role == "BORROWER":
            required_fields += ['current_postal_code', 'current_house_number', 'current_address', 'document_list']

        for field in required_fields:
            if not get_param(parameters, field):
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        # Build the profile
        first_name = get_param(parameters, 'first_name')
        last_name = get_param(parameters, 'last_name')
        email = get_param(parameters, 'email')
        iban = get_param(parameters, 'phone_number')
        phone_number = get_param(parameters, 'phone_number')

        if role == "INVESTOR":
            profile = InvestorProfile(first_name, last_name, email, iban, phone_number)
        else:
            current_postal_code = get_param(parameters, 'current_postal_code')
            current_house_number = get_param(parameters, 'current_house_number')
            current_address = get_param(parameters, 'current_address')
            documents = []
            for document in parameters['document_list']:
                documents.append(base64.decodestring(document))

            profile = BorrowersProfile(first_name, last_name, email, iban, phone_number,
                                       current_postal_code, current_house_number, current_address, documents)

        you = self.market_community.data_manager.you
        you.profile = profile

        # TODO(Martijn): broadcast it in the network

        return json.dumps({"success": True})

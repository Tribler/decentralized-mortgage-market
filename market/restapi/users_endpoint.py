import json

from twisted.web import http, resource

from market.models.investment import Investment, InvestmentStatus
from market.models.user import Role
from market.restapi import get_param


class UsersEndpoint(resource.Resource):
    """
    This class handles requests regarding users in the mortgage market community.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        return json.dumps({"users": [user.to_dictionary() for user in self.data_manager.users]})

    def getChild(self, path, request):
        return SpecificUserEndpoint(self.market_community, path)


class SpecificUserEndpoint(resource.Resource):
    """
    This class handles requests for a specific user, identified by their public key.
    """

    def __init__(self, market_community, pub_key):
        resource.Resource.__init__(self)
        self.pub_key = pub_key
        self.putChild("profile", SpecificUserProfileEndpoint(market_community, pub_key))
        self.putChild("investments", SpecificUserInvestmentsEndpoint(market_community, pub_key))

    def render_GET(self, request):
        user = self.market_community.data_manager.get_user(self.pub_key)
        if not user:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user not found"})

        return json.dumps({"user": user.to_dictionary()})


class SpecificUserProfileEndpoint(resource.Resource):
    """
    This class handles requests regarding the profile of a specific user.
    """

    def __init__(self, market_community, pub_key):
        resource.Resource.__init__(self)
        self.market_community = market_community
        self.pub_key = pub_key

    def render_GET(self, request):
        user = self.market_community.data_manager.get_user(self.pub_key)
        if not user:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user not found"})

        if not user.profile:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user does not have a profile"})

        return json.dumps({"profile": user.profile.to_dictionary()})


class SpecificUserInvestmentsEndpoint(resource.Resource):
    """
    This class handles requests regarding the investments of a specific user.
    """

    def __init__(self, market_community, pub_key):
        resource.Resource.__init__(self)
        self.market_community = market_community
        self.pub_key = pub_key

    def render_GET(self, request):
        user = self.market_community.data_manager.get_user(self.pub_key)
        if not user:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user not found"})

        if not user.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "this user is not an investor"})

        return json.dumps({"investments": [investment.to_dictionary() for investment in user.investments]})

    def render_PUT(self, request):
        user = self.market_community.data_manager.get_user(self.pub_key)
        if not user:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user not found"})

        if not user.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only investors can create new investments"})

        if not user == self.market_community.data_manager.you:  # Only you can create new investments...
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only you can create new investments"})

        parameters = http.parse_qs(request.content.read(), 1)
        required_fields = ['amount', 'duration', 'interest_rate', 'mortgage_id']
        for field in required_fields:
            if not get_param(parameters, field):
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        amount = get_param(parameters, 'amount')
        duration = get_param(parameters, 'duration')
        interest_rate = get_param(parameters, 'interest_rate')
        mortgage_id = get_param(parameters, 'mortgage_id')

        mortgage = self.market_community.data_manager.get_mortgage(mortgage_id)
        if not mortgage:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "mortgage not found"})

        investment = Investment(self.pub_key, amount, duration, interest_rate, mortgage, InvestmentStatus.PENDING)
        user.investments.append(investment)
        mortgage.investments.append(investment)

        #TODO(Martijn): broadcast it into the network

        return json.dumps({"success": True})

import json

from twisted.web import http, resource


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
        self.putChild("profile", SpecificUserProfileEndpoint(market_community, pub_key))


class SpecificUserProfileEndpoint(resource.Resource):
    """
    This class handles requests regarding the profile of a specific user.
    """

    def __init__(self, market_community, pub_key):
        resource.Resource.__init__(self)
        self.market_community = market_community
        self.pub_key = pub_key

    def render_GET(self, request):
        user = self.market_community.data_manager.get_user()
        if not user:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user not found"})

        if not user.profile:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user does not have a profile"})

        return json.dumps({"profile": user.profile.to_dictionary()})

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
        """
        .. http:get:: /users

        A GET request to this endpoint returns information about the known users in the system.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/users

            **Example response**:

            .. sourcecode:: javascript

                {
                    "users": [{
                        "id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "role": "BORROWER",
                        "time_added": "29-03-2017 13:59:39"
                    }, ...]
                }
        """
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

    def render_GET(self, request):
        """
        .. http:get:: /user/(string: user_id)

        A GET request to this endpoint returns information about a particular user in the system.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/user/a94a8fe5ccb19ba61c4c0873d391e987982fbbd3

            **Example response**:

            .. sourcecode:: javascript

                {
                    "user": {
                        "id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "role": "BORROWER",
                        "time_added": "29-03-2017 13:59:39"
                    }
                }
        """
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
        """
        .. http:get:: /user/(string: user_id)

        A GET request to this endpoint returns information about a profile of a user.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/user/a94a8fe5ccb19ba61c4c0873d391e987982fbbd3/profile

            **Example response**:

            .. sourcecode:: javascript

                {
                    "profile": {
                        "type": "investor",
                        "first_name": "Piet",
                        "last_name": "Tester",
                        "email": "piettester@gmail.com",
                        "iban": "NL90RABO0759395830",
                        "phone_number": "06685985936"
                    }
                }
        """
        user = self.market_community.data_manager.get_user(self.pub_key)
        if not user:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user not found"})

        if not user.profile:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "user does not have a profile"})

        return json.dumps({"profile": user.profile.to_dictionary()})

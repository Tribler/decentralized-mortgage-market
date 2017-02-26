from twisted.web import resource

from market.restapi.campaigns_endpoint import CampaignsEndpoint
from market.restapi.users_endpoint import UsersEndpoint


class RootEndpoint(resource.Resource):
    """
    This class represents the root endpoint of the decentralized mortgage market.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)

        child_handler_dict = {"users": UsersEndpoint, "campaigns": CampaignsEndpoint, "you": YouEndpoint}
        for path, child_cls in child_handler_dict.iteritems():
            self.putChild(path, child_cls(market_community))

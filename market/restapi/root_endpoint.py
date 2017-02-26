from twisted.web import resource

from market.community import ROLE_BANK
from market.restapi.campaigns_endpoint import CampaignsEndpoint
from market.restapi.users_endpoint import UsersEndpoint
from market.restapi.you_endpoint import YouEndpoint


class RootEndpoint(resource.Resource):
    """
    This class represents the root endpoint of the decentralized mortgage market.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)

        child_handler_dict = {"users": UsersEndpoint, "campaigns": CampaignsEndpoint, "you": YouEndpoint}
        for path, child_cls in child_handler_dict.iteritems():
            self.putChild(path, child_cls(market_community))

        if market_community.settings.role == ROLE_BANK:
            # Only activate this endpoint if we are a bank. Used to accept/reject loan requests offers.
            self.putChild("loanrequests", LoanRequestsEndpoint)

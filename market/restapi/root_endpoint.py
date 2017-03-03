import os

from twisted.web import resource
from twisted.web.static import File
from twisted.web.util import Redirect

from market.defs import BASE_DIR
from market.community import ROLE_BANK
from market.restapi.campaigns_endpoint import CampaignsEndpoint
from market.restapi.users_endpoint import UsersEndpoint
from market.restapi.you_endpoint import YouEndpoint
from market.restapi.loanrequests_endpoint import LoanRequestsEndpoint


class APIEndpoint(resource.Resource):

    def __init__(self, market_community):
        resource.Resource.__init__(self)

        child_handler_dict = {"users": UsersEndpoint, "campaigns": CampaignsEndpoint, "you": YouEndpoint}
        for path, child_cls in child_handler_dict.iteritems():
            self.putChild(path, child_cls(market_community))

        if market_community.role == ROLE_BANK:
            # Only activate this endpoint if we are a bank. Used to accept/reject loan requests offers.
            self.putChild("loanrequests", LoanRequestsEndpoint)



class RootEndpoint(resource.Resource):
    """
    This class represents the root endpoint of the decentralized mortgage market.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)

        self.putChild('', Redirect('/gui'))
        self.putChild('api', APIEndpoint(market_community))
        self.putChild('gui', File(os.path.join(BASE_DIR, 'webapp')))

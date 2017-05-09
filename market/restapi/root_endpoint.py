import os

from twisted.web import resource
from twisted.web.static import File
from twisted.web.util import Redirect

from market.defs import BASE_DIR
from market.restapi.campaigns_endpoint import CampaignsEndpoint
from market.restapi.users_endpoint import UsersEndpoint
from market.restapi.you_endpoint import YouEndpoint
from market.restapi.loanrequests_endpoint import LoanRequestsEndpoint
from market.restapi.mortgages_endpoint import MortgagesEndpoint
from market.restapi.investments_endpoint import InvestmentsEndpoint
from market.restapi.blocks_endpoint import BlocksEndpoint
from market.models.user import Role


class APIEndpoint(resource.Resource):

    def __init__(self, community):
        resource.Resource.__init__(self)

        child_handler_dict = {"users": UsersEndpoint,
                              "campaigns": CampaignsEndpoint,
                              "investments": InvestmentsEndpoint,
                              "blocks": BlocksEndpoint,
                              "you": YouEndpoint}
        for path, child_cls in child_handler_dict.iteritems():
            self.putChild(path, child_cls(community))

        if community.my_role == Role.FINANCIAL_INSTITUTION:
            # Only activate this endpoint if we are a bank. Used to accept/reject loan requests offers.
            self.putChild("loanrequests", LoanRequestsEndpoint(community))
            self.putChild("mortgages", MortgagesEndpoint(community))


class RootEndpoint(resource.Resource):
    """
    This class represents the root endpoint of the decentralized mortgage market.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)

        self.putChild('', Redirect('/gui'))
        self.putChild('api', APIEndpoint(community))
        self.putChild('gui', File(os.path.join(BASE_DIR, 'webapp', 'dist')))

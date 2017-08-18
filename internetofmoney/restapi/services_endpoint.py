import json
import os

from twisted.web import resource


class ServicesEndpoint(resource.Resource):
    """
    This class handles requests for money switch services.
    """

    def __init__(self, money_community):
        resource.Resource.__init__(self)
        self.money_community = money_community

    def render_GET(self, request):
        """
        Return known money switch services
        """
        services = []
        for candidate, candidate_services in self.money_community.candidate_services_map.iteritems():
            for bank_id, iban in candidate_services.iteritems():
                services.append({'ip': candidate.sock_addr[0], 'port': candidate.sock_addr[1],
                                 'iban': iban, 'bank_id': bank_id})

        return json.dumps({"services": services})

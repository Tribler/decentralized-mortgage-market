from twisted.web import resource

from internetofmoney.restapi.events_endpoint import EventsEndpoint
from internetofmoney.restapi.log_endpoint import LogEndpoint
from internetofmoney.restapi.services_endpoint import ServicesEndpoint
from internetofmoney.restapi.transactions_endpoint import TransactionsEndpoint


class RootEndpoint(resource.Resource):
    """
    The root endpoint of the IoM HTTP API is the root resource in the request tree.
    It will dispatch requests to the right child endpoint.
    """

    def __init__(self, database, cache_dir, money_community=None):
        resource.Resource.__init__(self)
        self.putChild("log", LogEndpoint(cache_dir))
        self.putChild("events", EventsEndpoint(database))
        self.putChild("transactions", TransactionsEndpoint(database))

        if money_community:
            self.putChild("services", ServicesEndpoint(money_community))

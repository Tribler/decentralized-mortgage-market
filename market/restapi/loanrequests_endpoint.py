import json

from twisted.web import http, resource

from market.models.loanrequest import LoanRequestStatus
from market.restapi import get_param


class LoanRequests(resource.Resource):
    """
    This class handles requests regarding loan requests in the mortgage market community.
    Only accessible by financial institutions.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        """
        .. http:get:: /loanrequests

        A GET request to this endpoint returns a list of loan requests. Only accessible by financial institutions.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/loanrequests

            **Example response**:

            .. sourcecode:: javascript

                {
                    "loan_requests": [{
                        "id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3_8948AB_16",
                        "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "mortgage_type": "FIXEDRATE",
                        "banks": ["ABN", "RABO"],
                        "description": "...",
                        "amount_wanted": 395000,
                        "status": "PENDING"
                    }, ...]
                }
        """
        return json.dumps({"loan_requests": [loan_request.to_dictionary() for
                                             loan_request in self.market_community.data_manager.get_loan_requests()]})

    def getChild(self, path, request):
        return SpecificLoanRequestEndpoint(self.market_community, path)


class SpecificLoanRequestEndpoint(resource.Resource):
    """
    This class handles requests for a specific loan request.
    """

    def __init__(self, market_community, loan_request_id):
        resource.Resource.__init__(self)
        self.market_community = market_community
        self.loan_request_id = loan_request_id

    def render_PATCH(self, request):
        """
        .. http:patch:: /loanrequests/(string: loan_request_id)

        A PATCH request to this endpoint will accept/reject a loan request.
        This is performed by a financial institution.

            **Example request**:

                .. sourcecode:: none

                    curl -X PATCH http://localhost:8085/loanrequests/a94a8fe5ccb19ba61c4c0873d391e987982fbbd3_8948AB_16
                    --data "state=ACCEPT"

            **Example response**:

                .. sourcecode:: javascript

                    {"success": True}
        """
        loan_request = self.market_community.data_manager.get_loan_request(self.loan_request_id)
        if not loan_request:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "loan request not found"})

        parameters = http.parse_qs(request.content.read(), 1)
        status = get_param(parameters, 'status')
        if not status:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing status parameter"})

        if status not in ['ACCEPT', 'REJECT']:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "invalid status value"})

        if loan_request.status[self.market_community.data_manager.you.id] != LoanRequestStatus.PENDING:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "loan request is already accepted/rejected"})

        if status == "ACCEPT":
            loan_request.status[self.market_community.data_manager.you.id] = LoanRequestStatus.ACCEPTED
        else:
            loan_request.status[self.market_community.data_manager.you.id] = LoanRequestStatus.REJECTED

        # TODO broadcast this into the network

        return json.dumps({"success": True})

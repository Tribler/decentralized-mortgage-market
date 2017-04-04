import json

from twisted.web import http, resource

from market.models.loanrequest import LoanRequestStatus
from market.models.mortgage import Mortgage, MortgageStatus


class LoanRequestsEndpoint(resource.Resource):
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
        return json.dumps({"loan_requests": [loan_request.to_dict() for
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
        self.loan_request_id = unicode(loan_request_id)

    def render_PATCH(self, request):
        """
        .. http:patch:: /loanrequests/(string: loan_request_id)

        A PATCH request to this endpoint will accept/reject a loan request.
        This is performed by a financial institution.

            **Example request**:

                .. sourcecode:: none

                    curl -X PATCH http://localhost:8085/loanrequests/a94a8fe5ccb19ba61c4c0873d391e987982fbbd3_8948AB_16
                    --data "status=ACCEPT"

            **Example response**:

                .. sourcecode:: javascript

                    {"success": True}
        """
        loan_request = self.market_community.data_manager.get_loan_request(self.loan_request_id)
        if not loan_request:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "loan request not found"})

        parameters = json.loads(request.content.read())
        status = parameters.get('status')
        if not status:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing status parameter"})

        if status not in ['ACCEPT', 'REJECT']:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "invalid status value"})

        if loan_request.status != LoanRequestStatus.PENDING:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "loan request is already accepted/rejected"})

        if status == "ACCEPT":
            loan_request.status = LoanRequestStatus.ACCEPTED
            # TODO: give the bank the opportunity to create a mortgage offer
            mortgage = Mortgage(loan_request.id,
                                loan_request.user_id,
                                self.market_community.my_user.id,
                                loan_request.house,
                                loan_request.amount_wanted,
                                loan_request.amount_wanted * 0.7,
                                loan_request.mortgage_type,
                                2.0,
                                2.0,
                                2.0,
                                120,
                                u'',
                                MortgageStatus.PENDING)
            user = self.market_community.data_manager.get_user(loan_request.user_id)
            user.mortgages.add(mortgage)
            self.market_community.send_mortgage_offer(loan_request, mortgage)
        else:
            loan_request.status = LoanRequestStatus.REJECTED
            self.market_community.send_loan_reject(loan_request)

        return json.dumps({"success": True})

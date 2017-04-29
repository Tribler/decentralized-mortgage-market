import json

from twisted.web import http, resource

from market.models.loanrequest import LoanRequestStatus
from market.models.mortgage import Mortgage, MortgageStatus
from market.restapi import split_composite_key


class LoanRequestsEndpoint(resource.Resource):
    """
    This class handles requests regarding loan requests in the mortgage market community.
    Only accessible by financial institutions.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

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
        return json.dumps({"loan_requests": [loan_request.to_dict(api_response=True) for
                                             loan_request in self.community.data_manager.get_loan_requests()]})

    def getChild(self, path, request):
        return SpecificLoanRequestEndpoint(self.community, path)


class SpecificLoanRequestEndpoint(resource.Resource):
    """
    This class handles requests for a specific loan request.
    """

    def __init__(self, community, loan_request_composite_key):
        resource.Resource.__init__(self)
        self.community = community
        self.loan_request_composite_key = loan_request_composite_key

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

        keys = split_composite_key(self.loan_request_composite_key)
        loan_request = self.community.data_manager.get_loan_request(*keys) if keys is not None else None
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

        if status == 'ACCEPT':
            required_fields = ['ltv', 'interest_rate', 'max_invest_rate', 'default_rate', 'duration', 'risk']
            for field in required_fields:
                if field not in parameters:
                    request.setResponseCode(http.BAD_REQUEST)
                    return json.dumps({"error": "missing %s parameter" % field})

        if loan_request.status != LoanRequestStatus.PENDING:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "loan request is already accepted/rejected"})

        if status == "ACCEPT":
            loan_request.status = LoanRequestStatus.ACCEPTED
            user = self.community.data_manager.get_user(loan_request.user_id)
            mortgage = Mortgage(user.mortgages.count(),
                                loan_request.user_id,
                                self.community.my_user.id,
                                loan_request.house,
                                loan_request.amount_wanted,
                                loan_request.amount_wanted * float(parameters['ltv']),
                                loan_request.mortgage_type,
                                parameters['interest_rate'],
                                parameters['max_invest_rate'],
                                parameters['default_rate'],
                                parameters['duration'],
                                parameters['risk'],
                                MortgageStatus.PENDING,
                                loan_request.id,
                                loan_request.user_id)
            user.mortgages.add(mortgage)
            self.community.offer_mortgage(loan_request, mortgage)
        else:
            loan_request.status = LoanRequestStatus.REJECTED
            self.community.reject_loan_request(loan_request)

        return json.dumps({"success": True})

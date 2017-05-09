import json

from twisted.web import http
from twisted.web import resource

from market.restapi import split_composite_key
from market.models.user import Role
from market.models.transfer import Transfer, TransferStatus


class InvestmentsEndpoint(resource.Resource):
    """
    This class handles requests regarding investments in the mortgage market community.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

    def getChild(self, path, request):
        return SpecificInvestmentEndpoint(self.community, path)

    def render_GET(self, request):
        """
        .. http:get:: /investments

        A GET request to this endpoint returns information about the ongoing investments.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/investments

            **Example response**:

            .. sourcecode:: javascript

                {
                    "investments": [{
                        "id": 2
                        "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "amount": 9000,
                        "duration": 24,
                        "interest_rate": 4.9,
                        "mortgage_id": "8593AB_89",
                        "status": "ACCEPTED"
                    }, ...]
                }
        """

        investment_dicts = []
        for investment in self.community.data_manager.get_investments():
            investment_dict = investment.to_dict(api_response=True)
            investment_dict["transfers"] = [transfer.to_dict(api_response=True) for transfer in investment.transfers]
            investment_dicts.append(investment_dict)

        return json.dumps({"investments": investment_dicts})


class SpecificInvestmentEndpoint(resource.Resource):
    """
    This class handles requests for a specific investment.
    """

    def __init__(self, community, investment_composite_key):
        resource.Resource.__init__(self)
        self.community = community
        self.investment_composite_key = investment_composite_key

        self.putChild("transfers", InvestmentTransfersEndpoint(community, investment_composite_key))

    def render_GET(self, request):
        """
        .. http:get:: /investments/(string: investment_id)

        A GET request to this endpoint returns detailled information about a specific investment.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/investments/2%20a94a8fe5ccb19ba61c4c0873d391e987982fbbd3

            **Example response**:

            .. sourcecode:: javascript

                {
                    "investment": {
                        "id": 2
                        "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "amount": 9000,
                        "duration": 24,
                        "interest_rate": 4.9,
                        "mortgage_id": "8593AB_89",
                        "status": "ACCEPTED"
                    }
                }
        """
        keys = split_composite_key(self.investment_composite_key)
        investment = self.community.data_manager.get_investment(*keys) if keys is not None else None
        if not investment:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "investment not found"})

        return json.dumps({"investment": investment.to_dict(api_response=True)})


class InvestmentTransfersEndpoint(resource.Resource):
    """
    This class handles requests regarding transfers for a specific investment in the mortgage market community.
    """

    def __init__(self, community, investment_composite_key):
        resource.Resource.__init__(self)
        self.community = community
        self.investment_composite_key = investment_composite_key

    def getChild(self, path, request):
        return SpecificInvestmentTransferEndpoint(self.community, self.investment_composite_key, path)

    def render_GET(self, request):
        """
        .. http:get:: /investments/(string: investment_id)/transfers

        A GET request to this endpoint returns a list of transfers related to a specific investment.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/investments/2%20a94a8fe5ccb19ba61c4c0873d391e987982fbbd3/transfers

            **Example response**:

            TODO

        """
        keys = split_composite_key(self.investment_composite_key)
        investment = self.community.data_manager.get_investment(*keys) if keys is not None else None
        if not investment:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "investment not found"})

        return json.dumps({"transfers": [transfer.to_dict(api_response=True) for transfer in investment.transfers]})

    def render_PUT(self, request):
        you = self.community.data_manager.you

        if not you.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only investors can create transfers"})

        parameters = json.loads(request.content.read())
        required_fields = ['iban', 'amount', 'investment_id', 'investment_user_id']
        for field in required_fields:
            if field not in parameters:
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        keys = split_composite_key(self.investment_composite_key)
        investment = self.community.data_manager.get_investment(*keys) if keys is not None else None
        if not investment:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "investment not found"})

        transfer = Transfer(you.transfers.count(), you.id, parameters['iban'], parameters['amount'],
                            investment.id, investment.user_id, TransferStatus.PENDING)

        you.transfers.add(transfer)
        investment.transfers.add(transfer)

        self.community.offer_transfer(transfer)

        return json.dumps({"success": True})


class SpecificInvestmentTransferEndpoint(resource.Resource):
    """
    This class handles requests for a specific transfer of an investment
    """
    def __init__(self, community, investment_composite_key, transfer_composite_key):
        resource.Resource.__init__(self)
        self.community = community
        self.investment_composite_key = investment_composite_key
        self.transfer_composite_key = transfer_composite_key

    def render_PATCH(self, request):
        you = self.community.data_manager.you

        if not you.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only investors can change transfers"})

        parameters = json.loads(request.content.read())
        status = parameters.get('status')
        if not status:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing status parameter"})

        if status not in ['ACCEPT', 'REJECT']:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "invalid status value"})

        keys = split_composite_key(self.investment_composite_key)
        investment = self.community.data_manager.get_investment(*keys) if keys is not None else None
        if not investment:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "investment not found"})

        keys = split_composite_key(self.transfer_composite_key)
        transfer = self.community.data_manager.get_transfer(*keys) if keys is not None else None
        if not transfer:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "transfer not found"})

        if transfer.status != TransferStatus.PENDING:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "transfer is already accepted/rejected"})

        if status == 'ACCEPT':
            transfer.status = TransferStatus.ACCEPTED
            self.community.accept_transfer(transfer)
        else:
            transfer.status = TransferStatus.REJECTED
            self.community.decline_transfer(transfer)

        return json.dumps({"success": True})

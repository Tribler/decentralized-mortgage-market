import json
import base64

from twisted.web import resource, http
from market.models.user import Role
from twisted.web.server import NOT_DONE_YET


class ContractsEndpoint(resource.Resource):
    """
    This class handles requests regarding contracts in the mortgage market community.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

    def getChild(self, path, request):
        return SpecificContractEndpoint(self.community, path)


class SpecificContractEndpoint(resource.Resource):
    """
    This class handles requests for a specific contract
    """
    def __init__(self, community, contract_id):
        resource.Resource.__init__(self)
        self.community = community
        self.contract_id = base64.urlsafe_b64decode(contract_id)

    def render_GET(self, request):
        you = self.community.data_manager.you

        contract = self.community.data_manager.get_contract(self.contract_id)
        if not contract:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "contract not found"})

        contract_dict = contract.to_dict(api_response=True)
        if you.role == Role.FINANCIAL_INSTITUTION:
            # Determine confirmations locally
            contract_dict["confirmations"] = self.community.find_confirmation_count(contract.id)
            return json.dumps({"contract": contract_dict})
        else:
            def on_traversal_response(response):
                _, confirmations = response
                contract_dict["confirmations"] = confirmations
                request.write(json.dumps({"contract": contract_dict}))
                request.finish()

            self.community.send_traversal_request(contract.id).addCallback(on_traversal_response)
            return NOT_DONE_YET

import json

from twisted.web import resource


class MortgagesEndpoint(resource.Resource):
    """
    This class handles requests regarding mortgages in the mortgage market community.
    Only accessible by financial institutions.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

    def render_GET(self, request):
        """
        .. http:get:: /mortgages

        A GET request to this endpoint returns a list of mortgages. Only accessible by financial institutions.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/mortgages

            **Example response**:

            .. sourcecode:: javascript

                {
                    "mortgages": [{
                        "id": 0,
                        "user_id": "TGliTmFDTFBLOgj_xZe05ZR4e1rx4oiEusMjbzp050aaX3AIO8Nc7l8A4jcsnjHL_EgRnzVtCfXGik6cAwTerOeDrMH5CLc1iWA=",
                        "bank_id": "TGliTmFDTFBLOgmEL13SpuuOSsgMKtwDb8HQIBLymMgd5ZLL2xTC5vQcLBJ1NioV-VcCeLmX5KdeqPzmEkVNOfXBmq-Het_RAyE=",
                        "interest_rate": 0.02,
                        "default_rate": 0.02,
                        "max_invest_rate": 0.02,
                        "amount": 200000,
                        "bank_amount": 175000,
                        "duration": 120,
                        "house": {
                            "seller_email": "user@example.com",
                            "seller_phone_number": "+123-45-6789012",
                            "house_number": "...",
                            "price": 200000,
                            "url": "...",
                            "postal_code": "...",
                            "address": "..."
                        },                    
                        "mortgage_type": "FIXEDRATE",
                        "status": "ACCEPTED",
                        "risk": "..."
                    }, ...]
                }
        """

        return json.dumps({"mortgages": [mortgage.to_dict(api_response=True) for
                                         mortgage in self.community.data_manager.get_mortgages()]})

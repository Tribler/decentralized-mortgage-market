import json

from datetime import datetime, timedelta
from twisted.web import http
from twisted.web import resource

from market.models.campaign import Campaign
from market.models.investment import InvestmentStatus
from market.restapi import get_param


class CampaignsEndpoint(resource.Resource):
    """
    This class handles requests regarding campaigns in the mortgage market community.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        """
        .. http:get:: /campaigns

        A GET request to this endpoint returns information about the ongoing campaigns.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/campaigns

            **Example response**:

            .. sourcecode:: javascript

                {
                    "campaigns": [{
                        "id": 8593AB_23,
                        "mortgage": {
                            "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                            "house": {
                                "postal_code": "8593AB",
                                "house_number": "23",
                                "address": "Teststraat, Rotterdam",
                                "price": 395000,
                                "url": "http://www.funda.nl/koop/hollandscheveld/huis-49981036-3e-zandwijkje-8/",
                                "seller_phone_number": "+31685938573",
                                "seller_email": "seller@gmail.com"
                            },
                            "bank": "ABN",
                            "amount": 395000,
                            "bank_amount": 200000,
                            "mortgage_type": "FIXEDRATE",
                            "interest_rate": 5.3,
                            "max_investment_rate": 4.3,
                            "default_rate": 4.3,
                            "duration": 120,
                            "risk": 300000,
                            "status": "ACCEPTED"
                        },
                        "amount": "195000",
                        "end_time": "1489934141",
                        "completed": False
                    }, ...]
                }
        """
        return json.dumps({"campaigns": [campaign.to_dict(include_investment=True)
                                         for campaign in self.market_community.data_manager.campaigns.values()]})

    def render_PUT(self, request):
        # TODO: remove? currently a campaign is created implicitly by the community

        """
        .. http:put:: /campaigns

        A PUT request to this endpoint will create a new campaign. Various parameters are required:
        - mortgage_id: the identifier of the mortgage. This mortgage should be yours and be accepted.

            **Example request**:

                .. sourcecode:: none

                    curl -X PUT http://localhost:8085/campaign --data "mortgage_id=8593AB_89"

            **Example response**:

                .. sourcecode:: javascript

                    {"success": True}
        """
        parameters = http.parse_qs(request.content.read(), 1)
        mortgage_id = get_param(parameters, 'mortgage_id')
        if not mortgage_id:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing mortgage id"})

        mortgage = self.market_community.data_manager.get_mortgage(mortgage_id)
        if not mortgage:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "mortgage with specified id not found"})

        if mortgage.user_id != self.market_community.data_manager.you.id:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "this mortgage is not yours"})

        if mortgage.campaign is not None:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "campaign for this mortgage already exists"})

        # Create the campaign
        end_date = datetime.now() + timedelta(days=30)
        finance_goal = mortgage.amount - mortgage.bank_amount
        campaign = Campaign(self.market_community.data_manager.you.id, mortgage, finance_goal, end_date, False)
        self.data_manager.campaigns.append(campaign)

        # TODO(Martijn): broadcast it into the network

        return json.dumps({"success": True})

    def getChild(self, path, request):
        return SpecificCampaignEndpoint(self.market_community, path)


class SpecificCampaignEndpoint(resource.Resource):
    """
    This class handles requests for a specific campaign.
    """

    def __init__(self, market_community, campaign_id):
        resource.Resource.__init__(self)
        self.market_community = market_community
        self.campaign_id = campaign_id

        self.putChild("investments", CampaignInvestmentsEndpoint(market_community, campaign_id))

    def render_GET(self, request):
        """
        .. http:get:: /campaigns/(string: campaign_id)

        A GET request to this endpoint returns detailled information about a specific campaign.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/campaigns/8593AB_89

            **Example response**:

            .. sourcecode:: javascript

                {
                    "campaign": {
                        "id": "8593AB_89",
                        "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "mortgage": {
                            "user_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                            "house": {
                                "postal_code": "8593AB",
                                "house_number": "23",
                                "address": "Teststraat, Rotterdam",
                                "price": 395000,
                                "url": "http://www.funda.nl/koop/hollandscheveld/huis-49981036-3e-zandwijkje-8/",
                                "seller_phone_number": "+31685938573",
                                "seller_email": "seller@gmail.com"
                            },
                            "bank": "ABN",
                            "amount": 395000,
                            "bank_amount": 200000,
                            "mortgage_type": "FIXEDRATE",
                            "interest_rate": 5.3,
                            "max_investment_rate": 4.3,
                            "default_rate": 4.3,
                            "duration": 120,
                            "risk": 300000,
                            "status": "ACCEPTED"
                        },
                        "amount": "195000",
                        "end_time": "1489934141",
                        "completed": False
                    }
                }
        """
        campaign = self.market_community.data_manager.get_campaign(self.campaign_id)
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        return json.dumps({"campaign": campaign.to_dict(include_investment=True)})


class CampaignInvestmentsEndpoint(resource.Resource):
    """
    This class handles requests regarding investments of a particular campaign
    """
    def __init__(self, market_community, campaign_id):
        resource.Resource.__init__(self)
        self.market_community = market_community
        self.campaign_id = campaign_id

    def getChild(self, path, request):
        return SpecificCampaignInvestmentEndpoint(self.market_community, self.campaign_id, path)

    def render_GET(self, request):
        """
        .. http:get:: /campaigns/(string: campaign_id)/investments

        A GET request to this endpoint returns a list of investments of a campaign.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/campaigns/8593AB_89/investments

            **Example response**:

            .. sourcecode:: javascript

                {
                    "investments": [{
                        "investor_id": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                        "amount": 9000,
                        "duration": 24,
                        "interest_rate": 4.9,
                        "mortgage_id": "8593AB_89",
                        "status": "ACCEPTED"
                    }, ...]
                }
        """
        campaign = self.market_community.data_manager.get_campaign(self.campaign_id)
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        return json.dumps({"investments": [investment.to_dict() for investment in campaign.mortgage.investments]})


class SpecificCampaignInvestmentEndpoint(resource.Resource):
    """
    This class handles requests for a specific investment in a campaign
    """
    def __init__(self, market_community, campaign_id, investment_id):
        resource.Resource.__init__(self)
        self.market_community = market_community
        self.campaign_id = campaign_id
        self.investment_id = investment_id

    def render_PATCH(self, request):
        """
        .. http:patch:: /campaigns/(string: campaign_id)/investments/(string: investment_id)

        A PATCH request to this endpoint will accept/reject an investment offer. This is performed by the borrower
        of a mortgage.

            **Example request**:

                .. sourcecode:: none

                    curl -X PATCH http://localhost:8085/campaigns/8948EE_43/investments/4344503b7e797ebf31582327a5baae35b11bda01
                    --data "state=ACCEPT"

            **Example response**:

                .. sourcecode:: javascript

                    {"success": True}
        """
        campaign = self.market_community.data_manager.get_campaign(self.campaign_id)
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        investment = campaign.mortgage.get_investment(self.investment_id)
        if not investment:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "investment not found"})

        parameters = json.loads(request.content.read())
        status = parameters.get('status')
        if not status:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing status parameter"})

        if status not in ['ACCEPT', 'REJECT']:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "invalid status value"})

        if investment.status != InvestmentStatus.PENDING:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "loan request is already accepted/rejected"})

        if status == "ACCEPT":
            investment.status = InvestmentStatus.ACCEPTED
            self.market_community.send_investment_accept(investment)
            self.market_community.send_campaign_update(campaign, investment)
        else:
            investment.status = InvestmentStatus.REJECTED
            self.market_community.send_investment_reject(investment)

        return json.dumps({"success": True})

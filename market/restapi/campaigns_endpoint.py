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
        return json.dumps({"campaigns": [user.to_dictionary() for user in self.data_manager.campaigns]})

    def render_PUT(self, request):
        parameters = http.parse_qs(request.content.read(), 1)
        mortgage_id = get_param(parameters, 'mortgage_id')
        if not mortgage_id:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing mortage id"})

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
        campaign = Campaign(self.market_community.data_manager.you, mortgage, finance_goal, end_date, False)
        self.data_manager.campaigns.append(campaign)

        #TODO(Martijn): broadcast it into the network

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
        campaign = self.market_community.data_manager.get_campaign(self.campaign_id)
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        return json.dumps({"campaign": campaign.to_dictionary()})


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
        campaign = self.market_community.data_manager.get_campaign(self.campaign_id)
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        return json.dumps({"investments": [investment.to_dictionary() for investment in campaign.mortage.investments]})


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
        Accept/reject an investment offer
        """
        campaign = self.market_community.data_manager.get_campaign(self.campaign_id)
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        investment = campaign.mortgage.get_investment(self.investment_id)
        if not investment:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "investment not found"})

        parameters = http.parse_qs(request.content.read(), 1)
        status = get_param(parameters, 'status')
        if not status:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing status parameter"})

        if status not in ['ACCEPT', 'REJECT']:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "invalid status value"})

        if investment.status[self.market_community.data_manager.you.id] != InvestmentStatus.PENDING:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "loan request is already accepted/rejected"})

        if status == "ACCEPT":
            investment.status = InvestmentStatus.ACCEPTED
        else:
            investment.status = InvestmentStatus.REJECTED

        # TODO broadcast this into the network

        return json.dumps({"success": True})

import json

from datetime import datetime, timedelta
from twisted.web import http
from twisted.web import resource

from market.models.campaign import Campaign
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
        self.campaign_id = campaign_id

    def render_GET(self, request):
        campaign = self.market_community.data_manager.get_campaign(self.campaign_id)
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        return json.dumps({"campaign": campaign.to_dictionary()})

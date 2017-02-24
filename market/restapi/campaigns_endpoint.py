import json

from twisted.web import http
from twisted.web import resource


class CampaignsEndpoint(resource.Resource):
    """
    This class handles requests regarding campaigns in the mortgage market community.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        return json.dumps({"campaigns": [user.to_dictionary() for user in self.data_manager.campaigns]})

    def getChild(self, path, request):
        return SpecificCampaignEndpoint(self.market_community, path)


class SpecificCampaignEndpoint(resource.Resource):
    """
    This class handles requests for a specific campaign.
    """

    def __init__(self, market_community, campaign_id):
        resource.Resource.__init__(self)
        self.campaign_id = campaign_id
        #self.putChild("mortgage", SpecificCampaignMortgageEndpoint(market_community, campaign_id))

    def render_GET(self, request):
        campaign = self.market_community.data_manager.get_campaign(self.campaign_id)
        if not campaign:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "campaign not found"})

        return json.dumps({"campaign": campaign.to_dictionary()})

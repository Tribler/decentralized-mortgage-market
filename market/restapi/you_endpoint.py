import base64
import json

from twisted.web import http, resource

from market.models.house import House
from market.models.investment import Investment, InvestmentStatus
from market.models.loanrequest import LoanRequest, LoanRequestStatus
from market.models.mortgage import MortgageStatus, MortgageType
from market.models.user import Role
from market.models.profile import Profile


class YouEndpoint(resource.Resource):
    """
    This class handles requests regarding your user in the mortgage market community.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

        self.putChild("profile", YouProfileEndpoint(market_community))
        self.putChild("investments", YouInvestmentsEndpoint(market_community))
        self.putChild("mortgages", YouMortgagesEndpoint(market_community))
        self.putChild("loanrequests", YouLoanRequestsEndpoint(market_community))
        self.putChild("campaigns", YouCampaignsEndpoint(market_community))

    def render_GET(self, request):
        return json.dumps({"you": self.market_community.data_manager.you.to_dict()})


class YouProfileEndpoint(resource.Resource):
    """
    This class handles requests regarding your profile.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        """
        .. http:get:: /user/(string: user_id)/profile

        A GET request to this endpoint returns information about your profile. Returns 404 if no profile is created.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/you/profile

            **Example response**:

            .. sourcecode:: javascript

                {
                    "profile": {
                        "type": "investor",
                        "first_name": "Piet",
                        "last_name": "Tester",
                        "email": "piettester@gmail.com",
                        "iban": "NL90RABO0759395830",
                        "phone_number": "06685985936"
                    }
                }
        """
        you = self.market_community.data_manager.you

        if not you.profile:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "you do not have a profile"})

        return json.dumps({"profile": you.profile.to_dict()})

    def render_PUT(self, request):
        """
        .. http:put:: /you/profile

        A PUT request to this endpoint will create a profile. Various parameters are required:
        - role: the role of the user, can be BORROWER or INVESTOR
        - first_name: the first name of the user
        - last_name: the last name of the user
        - email: the email address of the user
        - iban: the iban number of the user
        - phone_number: the phone number of the user

        If the user is a borrower, additional information is required:
        - current_postal_code: the postal code of the current address of the borrower
        - current_house_number: the house number of the current address of the borrower
        - current_address: the current address of the borrower
        - document_list: an array with base64-encoded files

            **Example request**:

                .. sourcecode:: none

                    curl -X PUT http://localhost:8085/you/profile --data "role=BORROWER&first_name=..."

            **Example response**:

                .. sourcecode:: javascript

                    {"success": True}
        """
        parameters = json.loads(request.content.getvalue())
        if 'role' not in parameters:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing role parameter"})

        role = parameters['role']
        required_fields = ['first_name', 'last_name', 'email', 'iban', 'phone_number']
        if role == "BORROWER":
            required_fields += ['current_postal_code', 'current_house_number', 'current_address', 'document_list']

        for field in required_fields:
            if field not in parameters:
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        # Build a new profile
        profile = Profile(parameters['first_name'],
                          parameters['last_name'],
                          parameters['email'],
                          parameters['iban'],
                          parameters['phone_number'],
                          parameters.get('current_postal_code'),
                          parameters.get('current_house_number'),
                          parameters.get('current_address'))

        you = self.market_community.data_manager.you
        if you.profile is None:
            you.profile = profile
        else:
            you.profile.merge(profile)

        # TODO: add documents to profile
        documents = []
        for document in parameters['document_list']:
            documents.append(base64.decodestring(document))

        return json.dumps({"success": True})


class YouInvestmentsEndpoint(resource.Resource):
    """
    This class handles requests regarding the investments of you.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        """
        .. http:get:: /you/investments

        A GET request to this endpoint returns a list of investments that you have made.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/you/investments

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
        you = self.market_community.data_manager.you
        if not you.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "this user is not an investor"})

        return json.dumps({"investments": [investment.to_dict() for investment in you.investments]})

    def render_PUT(self, request):
        you = self.market_community.data_manager.you

        if not you.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only investors can create new investments"})

        if you.profile is None:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "please create a profile prior to creating an investment offer"})

        parameters = json.loads(request.content.read())
        required_fields = ['amount', 'duration', 'interest_rate', 'campaign_id']
        for field in required_fields:
            if field not in parameters:
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        amount = parameters['amount']
        duration = parameters['duration']
        interest_rate = parameters['interest_rate']
        campaign_id = parameters['campaign_id']

        campaign = self.market_community.data_manager.get_campaign(campaign_id)
        if campaign is None:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "mortgage not found"})

        investment = Investment((u"%s_%s" % (campaign.id, campaign.investments.count())), you.id, amount, duration,
                                interest_rate, campaign.id, InvestmentStatus.PENDING)
        you.investments.add(investment)
        campaign.investments.add(investment)

        self.market_community.send_investment_offer(investment)

        return json.dumps({"success": True})


class YouLoanRequestsEndpoint(resource.Resource):
    """
    This class handles requests regarding the loan requests of you.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        you = self.market_community.data_manager.you

        if not you.role == Role.BORROWER:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "this user is not a borrower"})

        return json.dumps({"loan_requests": [loan_request.to_dict() for loan_request in you.loan_requests]})

    def render_PUT(self, request):
        you = self.market_community.data_manager.you

        if not you.role == Role.BORROWER:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only borrowers can create new loan requests"})

        if you.profile is None:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "please create a profile prior to creating a loan request"})

        parameters = json.loads(request.content.read())
        required_fields = ['postal_code', 'house_number', 'address', 'price', 'url', 'seller_phone_number',
                           'seller_email', 'mortgage_type', 'bank_id', 'description', 'amount_wanted']
        for field in required_fields:
            if field not in parameters:
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        if parameters['mortgage_type'] not in MortgageType.__members__:
            return json.dumps({"error": "unknown mortgage type"})

        mortgage_type = MortgageType[parameters['mortgage_type']]

        postal_code = parameters['postal_code']
        house_number = parameters['house_number']
        address = parameters['address']
        price = parameters['price']
        url = parameters['url']
        seller_phone_number = parameters['seller_phone_number']
        seller_email = parameters['seller_email']
        bank_id = parameters['bank_id']
        description = parameters['description']
        amount_wanted = parameters['amount_wanted']

        house = House(postal_code, house_number, address, price, url, seller_phone_number, seller_email)

        loan_request_id = u'%s_%s' % (you.id, you.loan_requests.count())
        loan_request = LoanRequest(loan_request_id, you.id, house, mortgage_type, bank_id,
                                   description, amount_wanted, LoanRequestStatus.PENDING)

        you.loan_requests.add(loan_request)

        self.market_community.send_loan_request(loan_request)

        # TODO(Martijn): Invoke TFTP here to send the documents to the banks

        return json.dumps({"success": True})


class YouMortgagesEndpoint(resource.Resource):
    """
    This class handles requests regarding your mortgages.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def getChild(self, path, request):
        return YouSpecificMortageEndpoint(self.market_community, path)

    def render_GET(self, request):
        you = self.market_community.data_manager.you
        return json.dumps({"mortgages": [mortgage.to_dict() for mortgage in you.mortgages]})


class YouSpecificMortageEndpoint(resource.Resource):
    """
    This class handles requests regarding a specific mortgage.
    """
    def __init__(self, market_community, mortgage_id):
        resource.Resource.__init__(self)
        self.market_community = market_community
        self.mortgage_id = unicode(mortgage_id)

    def render_PATCH(self, request):
        """
        Accept/reject a mortgage offer
        """
        mortgage = self.market_community.data_manager.get_mortgage(self.mortgage_id)
        if not mortgage:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "mortgage not found"})

        parameters = json.loads(request.content.read())
        status = parameters.get('status')
        if not status:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing status parameter"})

        if status not in ['ACCEPT', 'REJECT']:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "invalid status value"})

        if mortgage.status != MortgageStatus.PENDING:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "mortgage is already accepted/rejected"})

        if status == "ACCEPT":
            mortgage.status = MortgageStatus.ACCEPTED
            self.market_community.send_mortgage_accept(mortgage)
        else:
            mortgage.status = MortgageStatus.REJECTED
            self.market_community.send_mortgage_reject(mortgage)

        return json.dumps({"success": True})


class YouCampaignsEndpoint(resource.Resource):
    """
    This class handles requests regarding your campaigns.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        you = self.market_community.data_manager.you
        campaigns = []
        for campaign in you.campaigns:
            campaign_dict = campaign.to_dict(include_investment=True)
            campaign_dict['investments'] = [investment.to_dict() for investment in campaign.investments]
            campaigns.append(campaign_dict)
        return json.dumps({"campaigns": campaigns})

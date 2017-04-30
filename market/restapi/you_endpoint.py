import base64
import json

from base64 import urlsafe_b64decode
from twisted.web import http, resource

from market.models.house import House
from market.models.investment import Investment, InvestmentStatus
from market.models.loanrequest import LoanRequest, LoanRequestStatus
from market.models.mortgage import MortgageStatus, MortgageType
from market.models.user import Role
from market.models.profile import Profile
from market.restapi import split_composite_key


class YouEndpoint(resource.Resource):
    """
    This class handles requests regarding your user in the mortgage market community.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

        self.putChild("profile", YouProfileEndpoint(community))
        self.putChild("investments", YouInvestmentsEndpoint(community))
        self.putChild("mortgages", YouMortgagesEndpoint(community))
        self.putChild("loanrequests", YouLoanRequestsEndpoint(community))
        self.putChild("campaigns", YouCampaignsEndpoint(community))

    def render_GET(self, request):
        return json.dumps({"you": self.community.data_manager.you.to_dict(api_response=True)})


class YouProfileEndpoint(resource.Resource):
    """
    This class handles requests regarding your profile.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

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
        you = self.community.data_manager.you

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

        you = self.community.data_manager.you
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

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

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
        you = self.community.data_manager.you
        if not you.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "this user is not an investor"})

        return json.dumps({"investments": [investment.to_dict(api_response=True) for investment in you.investments]})

    def render_PUT(self, request):
        you = self.community.data_manager.you

        if not you.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only investors can create new investments"})

        if you.profile is None:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "please create a profile prior to creating an investment offer"})

        parameters = json.loads(request.content.read())
        required_fields = ['amount', 'interest_rate', 'campaign_id', 'campaign_user_id']
        for field in required_fields:
            if field not in parameters:
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        amount = parameters['amount']
        interest_rate = parameters['interest_rate']
        campaign_id = parameters['campaign_id']
        campaign_user_id = urlsafe_b64decode(str(parameters['campaign_user_id']))

        campaign = self.community.data_manager.get_campaign(campaign_id, campaign_user_id)
        if campaign is None:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "mortgage not found"})

        investment = Investment(you.investments.count(), you.id, amount, 0,
                                interest_rate, campaign.id, campaign.user_id, InvestmentStatus.PENDING)
        you.investments.add(investment)
        campaign.investments.add(investment)

        self.community.offer_investment(investment)

        return json.dumps({"success": True})


class YouLoanRequestsEndpoint(resource.Resource):
    """
    This class handles requests regarding the loan requests of you.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

    def render_GET(self, request):
        you = self.community.data_manager.you

        if not you.role == Role.BORROWER:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "this user is not a borrower"})

        return json.dumps({"loan_requests": [loan_request.to_dict(api_response=True) for loan_request in you.loan_requests]})

    def render_PUT(self, request):
        you = self.community.data_manager.you

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
        bank_id = urlsafe_b64decode(str(parameters['bank_id']))
        description = parameters['description']
        amount_wanted = parameters['amount_wanted']

        house = House(postal_code, house_number, address, price, url, seller_phone_number, seller_email)

        loan_request = LoanRequest(you.loan_requests.count(), you.id, house, mortgage_type, bank_id,
                                   description, amount_wanted, LoanRequestStatus.PENDING)

        you.loan_requests.add(loan_request)

        self.community.offer_loan_request(loan_request)

        # TODO(Martijn): Invoke TFTP here to send the documents to the banks

        return json.dumps({"success": True})


class YouMortgagesEndpoint(resource.Resource):
    """
    This class handles requests regarding your mortgages.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

    def getChild(self, path, request):
        return YouSpecificMortageEndpoint(self.community, path)

    def render_GET(self, request):
        you = self.community.data_manager.you
        return json.dumps({"mortgages": [mortgage.to_dict(api_response=True) for mortgage in you.mortgages]})


class YouSpecificMortageEndpoint(resource.Resource):
    """
    This class handles requests regarding a specific mortgage.
    """
    def __init__(self, community, morgage_composite_key):
        resource.Resource.__init__(self)
        self.community = community
        self.morgage_composite_key = morgage_composite_key

    def render_PATCH(self, request):
        """
        Accept/reject a mortgage offer
        """
        keys = split_composite_key(self.morgage_composite_key)
        mortgage = self.community.data_manager.get_mortgage(*keys) if keys is not None else None
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
            self.community.accept_mortgage(mortgage)
        else:
            mortgage.status = MortgageStatus.REJECTED
            self.community.reject_mortgage(mortgage)

        return json.dumps({"success": True})


class YouCampaignsEndpoint(resource.Resource):
    """
    This class handles requests regarding your campaigns.
    """

    def __init__(self, community):
        resource.Resource.__init__(self)
        self.community = community

    def render_GET(self, request):
        you = self.community.data_manager.you
        campaigns = []
        for campaign in you.campaigns:
            campaign_dict = campaign.to_dict(api_response=True)
            campaign_dict['investments'] = [investment.to_dict(api_response=True) for investment in campaign.investments]
            campaigns.append(campaign_dict)
        return json.dumps({"campaigns": campaigns})

import base64
import json

from twisted.web import http, resource

from market.models.house import House
from market.models.investment import Investment, InvestmentStatus
from market.models.loanrequest import LoanRequest, LoanRequestStatus
from market.models.profile import InvestorProfile, BorrowersProfile
from market.models.user import Role
from market.restapi import get_param


class YouEndpoint(resource.Resource):
    """
    This class handles requests regarding your user in the mortgage market community.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

        self.putChild("profile", YouProfileEndpoint(market_community))
        self.putChild("investments", YouInvestmentsEndpoint(market_community))

    def render_GET(self, request):
        return json.dumps({"you": self.market_community.data_manager.you.to_dictionary()})


class YouProfileEndpoint(resource.Resource):
    """
    This class handles requests regarding your profile.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        you = self.market_community.data_manager.you

        if not you.profile:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "you do not have a profile"})

        return json.dumps({"profile": you.profile.to_dictionary()})

    def render_PUT(self, request):
        parameters = http.parse_qs(request.content.read(), 1)
        if not get_param(parameters, 'role'):
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "missing role parameter"})

        role = get_param(parameters, 'role')
        required_fields = ['first_name', 'last_name', 'email', 'iban', 'phone_number']
        if role == "BORROWER":
            required_fields += ['current_postal_code', 'current_house_number', 'current_address', 'document_list']

        for field in required_fields:
            if not get_param(parameters, field):
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        # Build the profile
        first_name = get_param(parameters, 'first_name')
        last_name = get_param(parameters, 'last_name')
        email = get_param(parameters, 'email')
        iban = get_param(parameters, 'phone_number')
        phone_number = get_param(parameters, 'phone_number')

        if role == "INVESTOR":
            profile = InvestorProfile(first_name, last_name, email, iban, phone_number)
        else:
            current_postal_code = get_param(parameters, 'current_postal_code')
            current_house_number = get_param(parameters, 'current_house_number')
            current_address = get_param(parameters, 'current_address')
            documents = []
            for document in parameters['document_list']:
                documents.append(base64.decodestring(document))

            profile = BorrowersProfile(first_name, last_name, email, iban, phone_number,
                                       current_postal_code, current_house_number, current_address, documents)

        you = self.market_community.data_manager.you
        you.profile = profile

        # TODO(Martijn): broadcast it in the network

        return json.dumps({"success": True})


class YouInvestmentsEndpoint(resource.Resource):
    """
    This class handles requests regarding the investments of you.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        you = self.market_community.data_manager.you
        if not you.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "this user is not an investor"})

        return json.dumps({"investments": [investment.to_dictionary() for investment in you.investments]})

    def render_PUT(self, request):
        you = self.market_community.data_manager.you

        if not you.role == Role.INVESTOR:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only investors can create new investments"})

        parameters = http.parse_qs(request.content.read(), 1)
        required_fields = ['amount', 'duration', 'interest_rate', 'mortgage_id']
        for field in required_fields:
            if not get_param(parameters, field):
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        amount = get_param(parameters, 'amount')
        duration = get_param(parameters, 'duration')
        interest_rate = get_param(parameters, 'interest_rate')
        mortgage_id = get_param(parameters, 'mortgage_id')

        mortgage = self.market_community.data_manager.get_mortgage(mortgage_id)
        if not mortgage:
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "mortgage not found"})

        investment = Investment(self.pub_key, amount, duration, interest_rate, mortgage, InvestmentStatus.PENDING)
        you.investments.append(investment)
        mortgage.investments.append(investment)

        #TODO(Martijn): broadcast it into the network

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

        return json.dumps({"loan_requests": [loan_request.to_dictionary() for loan_request in you.loan_requests]})

    def render_PUT(self, request):
        you = self.market_community.data_manager.you

        if not you.role == Role.BORROWER:
            request.setResponseCode(http.BAD_REQUEST)
            return json.dumps({"error": "only borrowers can create new loan requests"})

        parameters = http.parse_qs(request.content.read(), 1)
        required_fields = ['postal_code', 'house_number', 'address', 'price', 'url', 'seller_phone_number',
                           'seller_email', 'mortgage_type', 'banks', 'description', 'amount_wanted']
        for field in required_fields:
            if not get_param(parameters, field):
                request.setResponseCode(http.BAD_REQUEST)
                return json.dumps({"error": "missing %s parameter" % field})

        postal_code = get_param(parameters, 'postal_code')
        house_number = get_param(parameters, 'house_number')
        address = get_param(parameters, 'address')
        price = get_param(parameters, 'price')
        url = get_param(parameters, 'url')
        seller_phone_number = get_param(parameters, 'seller_phone_number')
        seller_email = get_param(parameters, 'seller_email')
        mortgage_type = get_param(parameters, 'mortgage_type')
        banks = get_param(parameters, 'banks')
        description = get_param(parameters, 'description')
        amount_wanted = get_param(parameters, 'amount_wanted')

        house = House(postal_code, house_number, address, price, url, seller_phone_number, seller_email)
        loan_request = LoanRequest(you, house, mortgage_type, banks, description,
                                   amount_wanted, LoanRequestStatus.PENDING)
        you.loan_requests.append(loan_request)

        #TODO(Martijn): broadcast it into the network
        #TODO(Martijn): Invoke TFTP here to send the documents to the banks

        return json.dumps({"success": True})

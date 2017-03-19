from market.models.user import User


class MarketDataManager:
    """
    This class stores and manages all the data for the decentralized mortgage market.
    It should be replaced by a nice ORM database at one point in the future.
    """

    def __init__(self, your_user):
        self.you = your_user
        self.users = {}
        self.campaigns = {}

    def get_user(self, id):
        """
        Get a specific user from the database
        :param id: the public key of the user
        :return: the User object with the specified public key or None if it is not found
        """
        return self.users.get(id)

    def create_user(self):
        """
        Create a new user with a fresh keypair.
        :return: the new user created.
        """
        new_user = User.generate()
        self.users[new_user.id] = new_user
        return new_user

    def get_campaign(self, campaign_id):
        """
        Get a specific campaign with a specified id
        :param campaign_id: the id of the campaign to search for
        :return: a Campaign object or None if no campaign could be found
        """
        # TODO: fix this...
        c = self.campaigns.get(campaign_id)
        if c:
            return c

        for campaign in self.you.campaigns:
            if campaign.mortgage.id == campaign_id:
                return campaign

    def get_mortgage(self, mortgage_id):
        """
        Get a specific mortgage with a specified id
        :param mortgage_id: the id of the mortgage to search for
        :return: a Mortgage object or None if no mortgage could be found
        """
        for user in self.users.values() + [self.you]:
            for mortgage in user.mortgages:
                if mortgage.id == mortgage_id:
                    return mortgage

    def get_investment(self, investment_id):
        """
        Get a specific investment with a specified id
        :param investment_id: the id of the investment to search for
        :return: an Investment object or None if no investment could be found
        """
        for user in self.users.values() + [self.you]:
            for mortgage in user.mortgages:
                investment = mortgage.get_investment(investment_id)
                if investment:
                    return investment

    def get_loan_requests(self):
        """
        Get all loan requests in the market.
        :return: a list with LoanRequest objects
        """
        loan_requests = []
        for user in self.users.values():
            for loan_request in user.loan_requests:
                loan_requests.append(loan_request)
        return loan_requests

    def get_loan_request(self, loan_request_id):
        """
        Get a loan requests in the market.
        :param loan_request_id: the of the loan request to search for
        :return: a LoanRequest object or None if no loan request could be found
        """
        for user in self.users.values() + [self.you]:
            for loan_request in user.loan_requests:
                if loan_request.id == loan_request_id:
                    return loan_request

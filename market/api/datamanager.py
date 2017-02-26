from market.models.user import User


class MarketDataManager:
    """
    This class stores and manages all the data for the decentralized mortgage market.
    It should be replaced by a nice ORM database at one point in the future.
    """

    def __init__(self, your_member):
        self.you = your_member
        self.users = []
        self.campaigns = []

    def get_user(self, id):
        """
        Get a specific user from the database
        :param id: the public key of the user
        :return: the User object with the specified public key or None if it is not found
        """
        for user in self.users:
            if user.id == id:
                return user
        return None

    def create_user(self):
        """
        Create a new user with a fresh keypair.
        :return: the new user created.
        """
        new_user = User.generate()
        self.users.append(new_user)
        return new_user

    def get_campaign(self, campaign_id):
        """
        Get a specific campaign with a specified id
        :param campaign_id: the id of the campaign to search for
        :return: a Campaign object or None if no campaign could be found
        """
        for campaign in self.campaigns:
            if campaign.id == campaign_id:
                return campaign
        return None

    def get_mortgage(self, mortgage_id):
        """
        Get a specific mortgage with a specified id
        :param mortgage_id: the id of the mortgage to search for
        :return: a Mortgage object or None if no mortgage could be found
        """
        for user in self.users:
            for mortgage in user.mortgages:
                if mortgage.id == mortgage_id:
                    return mortgage
        return None

    def get_loan_requests(self):
        """
        Get all loan requests in the market.
        :return: a list with LoanRequest objects
        """
        loan_requests = []
        for user in self.users:
            for loan_request in user.loan_requests:
                loan_requests.append(loan_request)
        return loan_requests

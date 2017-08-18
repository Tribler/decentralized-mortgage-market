import json
import os

from twisted.web import resource


class TransactionsEndpoint(resource.Resource):
    """
    This class handles requests for transactions, which are read from the database.
    """

    def __init__(self, database):
        resource.Resource.__init__(self)
        self.database = database

    def render_GET(self, request):
        """
        Read and return transactions from the database
        """
        limit = 100
        if 'limit' in request.args:
            limit = int(request.args['q'][0])

        transactions = [{'timestamp': timestamp, 'txid': txid, 'from_iban': from_iban,
                         'to_iban': to_iban, 'amount': amount, 'description': description} for timestamp, txid,
                                                                                               from_iban, to_iban,
                                                                                               amount, description in
                        self.database.get_transactions(limit=limit)]

        return json.dumps({"transactions": transactions})

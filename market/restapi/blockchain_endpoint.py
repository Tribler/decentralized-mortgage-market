import json

from twisted.web import resource


class BlockchainEndpoint(resource.Resource):
    """
    This class handles requests regarding the blockchain in the mortgage market community.
    """

    def __init__(self, market_community):
        resource.Resource.__init__(self)
        self.market_community = market_community

    def render_GET(self, request):
        """
        .. http:get:: /blockchain

        A GET request to this endpoint returns a list of block in the blockchain.

            **Example request**:

            .. sourcecode:: none

                curl -X GET http://localhost:8085/blockchain

            **Example response**:

            .. sourcecode:: javascript

                {
                    "blockchain": [{
                        "signature": "n4h7Ny12uG8zXbBNoxiVF15Hgbib7KJK3n77uIK3T0mUb1YcKwjPycR_tt9JriQM8BzLbIenNmS7gFOjbMCRDA==",
                        "document": "CAASSkxpYk5hQ0xQSzqDV3qMldg2nCTpv0ftMTT9x4N-RLVW-C9i4HxHESEwF2OBllie567j-V4OyFp81Uy5Myn_C_VaE9....",
                        "previous_hash_signee": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                        "sequence_number_signee": 0,
                        "signee": "TGliTmFDTFBLOoQTOuADyUMAluJi5-OS6uXxGTiYQ9sCFtxrBgC4myEbbSotViSYtBHAgxwerbpYdtS7vnhwRuBEkJ6pmq0JyLw="
                    }, ...]
                }
        """

        return json.dumps({"blockchain": [block.to_dict(api_response=True) for
                                          block in self.market_community.data_manager.get_blocks()]})

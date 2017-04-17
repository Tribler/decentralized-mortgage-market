from storm.properties import Int, RawStr


class BestChain(object):
    """
    This class represents the head of the best blockchain
    """

    __storm_table__ = 'best_chain'
    id = Int(primary=True)
    block_id = RawStr()
    height = Int()
    score = Int()

    def __init__(self, block_id, height, score):
        # The best chain table has only one entry with id=0
        self.id = 0
        self.block_id = block_id
        self.height = height
        self.score = score

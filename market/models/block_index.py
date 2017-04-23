from storm.properties import Int, RawStr


class BlockIndex(object):
    """
    This class is used to keep track of which blocks are on the best chain
    """

    __storm_table__ = 'block_index'
    block_id = RawStr(primary=True)
    height = Int()
    score = Int()

    def __init__(self, block_id, height, score=0):
        self.block_id = block_id
        self.height = height
        self.score = score

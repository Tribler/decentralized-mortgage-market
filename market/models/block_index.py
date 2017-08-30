from storm.properties import Int, RawStr


class BlockIndex(object):
    """
    This class is used to keep track of which blocks are on the best chain
    """

    __storm_table__ = 'block_index'
    block_id = RawStr(primary=True)
    height = Int()

    def __init__(self, block_id, height):
        self.block_id = block_id
        self.height = height

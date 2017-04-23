from storm.properties import RawStr, Int


class BlockContract(object):
    __storm_table__ = 'block_contract'
    __storm_primary__ = 'block_id', 'contract_id'
    block_id = RawStr()
    contract_id = RawStr()
    position = Int()

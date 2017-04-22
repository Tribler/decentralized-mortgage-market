from storm.store import Store


# Fixes an issues that only seems to occur when we have multiple contract in a single block.
# See also: https://bugs.launchpad.net/storm/+bug/1334020
class MarketStore(Store):

    def flush(self):
        for key in self._order.keys():
            for obj in key:
                for v in obj.values():
                    if type(v) == dict and 'flush_order' in v:
                        v.pop('flush_order')

        super(MarketStore, self).flush()

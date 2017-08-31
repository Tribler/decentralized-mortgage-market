from dispersy.payload import Payload


class CrawlRequestPayload(Payload):
    """
    Request a crawl of blocks starting with a specific sequence number or the first if 0.
    """
    class Implementation(Payload.Implementation):
        def __init__(self, meta, requested_sequence_number):
            super(CrawlRequestPayload.Implementation, self).__init__(meta)
            self.requested_sequence_number = requested_sequence_number


class HalfBlockPayload(Payload):
    """
    Payload for message that ships a half block
    """
    class Implementation(Payload.Implementation):
        def __init__(self, meta, block):
            super(HalfBlockPayload.Implementation, self).__init__(meta)
            self.block = block

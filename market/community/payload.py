from __future__ import absolute_import

from dispersy.payload import Payload


class ProtobufPayload(Payload):
    class Implementation(Payload.Implementation):
        def __init__(self, meta, dictionary):
            super(Payload.Implementation, self).__init__(meta)
            self._dictionary = dictionary

        @property
        def dictionary(self):
            return self._dictionary

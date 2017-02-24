class Document(object):
    """
    This class represents a document that is sent from borrowers to the bank.
    """

    def __init__(self, mime, data, name):
        self._mime = mime
        self._data = data
        self._name = name

    @property
    def mime(self):
        return self._mime

    @property
    def data(self):
        return self._data

    @property
    def name(self):
        return self._name

    def to_dictionary(self):
        return {
            "mime": self._mime,
            "name": self._name,
        }

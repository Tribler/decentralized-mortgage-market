class Document(object):
    """
    This class represents a document that is sent from borrowers to the bank.
    """

    def __init__(self, mime, name, data):
        self._mime = mime
        self._name = name
        self._data = data

    @property
    def mime(self):
        return self._mime

    @property
    def name(self):
        return self._name

    @property
    def data(self):
        return self._data

    def to_dict(self):
        return {
            "mime": self._mime,
            "name": self._name,
            "data": self._data
        }

    @staticmethod
    def from_dict(document_dict):
        return Document(document_dict['mime'],
                        document_dict['name'],
                        document_dict['data'])



class Profile(object):
    """
    Base class for a profile. Each profile is associated with a user.
    """

    def __init__(self, first_name, last_name, email, iban, phone_number):
        assert isinstance(first_name, unicode)
        assert isinstance(last_name, unicode)
        assert isinstance(email, str)
        assert isinstance(iban, str)
        assert isinstance(phone_number, str)

        self._first_name = first_name
        self._last_name = last_name
        self._email = email
        self._iban = iban
        self._phone_number = phone_number

    @property
    def first_name(self):
        return self._first_name

    @property
    def last_name(self):
        return self._last_name

    @property
    def email(self):
        return self._email

    @property
    def iban(self):
        return self._iban

    @property
    def phone_number(self):
        return self._phone_number


class InvestorProfile(Profile):
    """
    This class represents an investor, someone who wants to lend money to users.
    """
    def to_dictionary(self):
        return {
            "type": "investor",
            "first_name": self._first_name,
            "last_name": self._last_name,
            "email": self._email,
            "iban": self._iban,
            "phone_number": self._phone_number
        }


class BorrowersProfile(Profile):
    """
    This class represents a borrower of money, someone looking for a mortgage and investors.
    A borrower requires additional information.
    """
    def __init__(self, first_name, last_name, email, iban, phone_number, current_postal_code, current_house_number,
                 current_address, document_list):
        super(BorrowersProfile, self).__init__(first_name, last_name, email, iban, phone_number)

        self._current_postal_code = current_postal_code
        self._current_house_number = current_house_number
        self._current_address = current_address
        self._document_list = document_list

    @property
    def current_postal_code(self):
        return self._current_postal_code

    @property
    def current_house_number(self):
        return self._current_house_number

    @property
    def current_address(self):
        return self._current_address

    @property
    def document_list(self):
        return self._document_list

    def add_document(self, document):
        self._document_list.append(document)

    def to_dictionary(self):
        return {
            "type": "borrower",
            "first_name": self._first_name,
            "last_name": self._last_name,
            "email": self._email,
            "iban": self._iban,
            "phone_number": self._phone_number,
            "current_postal_code": self._current_postal_code,
            "current_house_number": self.current_house_number,
            "current_address": self.current_address,
            "documents": [document.to_dictionary() for document in self._document_list]
        }

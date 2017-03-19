

class House(object):
    """
    This class represents a house for which a mortgage is created.
    """

    def __init__(self, postal_code, house_number, address, price, url, seller_phone_number, seller_email):
        self._postal_code = postal_code
        self._house_number = house_number
        self._address = address
        self._price = price
        self._url = url
        self._seller_phone_number = seller_phone_number
        self._seller_email = seller_email

    @property
    def id(self):
        return self._postal_code + "_" + self._house_number

    @property
    def postal_code(self):
        return self._postal_code

    @property
    def house_number(self):
        return self._house_number

    @property
    def address(self):
        return self._address

    @property
    def price(self):
        return self._price

    @property
    def url(self):
        return self._url

    @property
    def seller_phone_number(self):
        return self._seller_phone_number

    @property
    def seller_email(self):
        return self._seller_email

    def to_dict(self):
        return {
            "postal_code": self._postal_code,
            "house_number": self._house_number,
            "address": self._address,
            "price": self._price,
            "url": self._url,
            "seller_phone_number": self._seller_phone_number,
            "seller_email": self._seller_email
        }

    @staticmethod
    def from_dict(house_dict):
        return House(house_dict['postal_code'],
                     house_dict['house_number'],
                     house_dict['address'],
                     house_dict['price'],
                     house_dict['url'],
                     house_dict['seller_phone_number'],
                     house_dict['seller_email'])

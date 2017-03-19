from storm.properties import Int, Unicode, Float


class House(object):
    """
    This class represents a house for which a mortgage is created.
    """

    __storm_table__ = "house"
    id = Int(primary=True)
    postal_code = Unicode()
    house_number = Unicode()
    address = Unicode()
    price = Float()
    url = Unicode()
    seller_phone_number = Unicode()
    seller_email = Unicode()

    def __init__(self, postal_code, house_number, address, price, url, seller_phone_number, seller_email):
        self.postal_code = postal_code
        self.house_number = house_number
        self.address = address
        self.price = price
        self.url = url
        self.seller_phone_number = seller_phone_number
        self.seller_email = seller_email

    def to_dict(self):
        return {
            "postal_code": self.postal_code,
            "house_number": self.house_number,
            "address": self.address,
            "price": self.price,
            "url": self.url,
            "seller_phone_number": self.seller_phone_number,
            "seller_email": self.seller_email
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

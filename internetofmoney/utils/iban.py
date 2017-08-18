from schwifty import IBAN


class IBANUtil(object):

    @staticmethod
    def get_bank_id(iban):
        return iban[4:8]

    @staticmethod
    def is_valid_iban(iban):
        try:
            return IBAN(iban).validate()
        except ValueError:
            return False

import os
import hashlib

from base64 import urlsafe_b64decode

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))

DEFAULT_REST_API_PORT = 8085
DEFAULT_DISPERSY_PORT = 7795

VERIFIED_BANKS = {'ABN-Amro': 'TGliTmFDTFBLOoc8OkIAtq9_8j5NmUG6tUWR473jLdUeyzqoHT0bVBoIb6bc4fVAV_9ejYro-XXqfl7yKmyblEoUH_AcgnEzzN0=',
                  'Rabobank': 'TGliTmFDTFBLOrhXMbHGgk_Pq0TXYqMOCY7FTbtvwe3sXm9XbbzO0bkPsYfofTeAUUDtcBiPCEP2ntMQLdF-oeVr5FeXPoEbwpE=',
                  'ING': 'TGliTmFDTFBLOiNVoxDL3S0wHOcEN7bdciOQzZfNYqyNUM9eQGmUNC5sRtKsb-KXzu8z1UJ-3ffNMzrtTXN-Vc9O8qmN3ymUKa4='}

VERIFIED_BANKS = {k : urlsafe_b64decode(v) for k, v in VERIFIED_BANKS.iteritems()}
VERIFIED_BANK_IDS = {k : hashlib.sha256(v).digest() for k, v in VERIFIED_BANKS.iteritems()}

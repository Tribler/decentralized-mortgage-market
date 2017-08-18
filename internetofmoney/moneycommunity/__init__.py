"""
This community is responsible for finding money routers.
"""
import random
import string


def generate_txid(length=10):
    """
    Generate a random transaction ID
    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

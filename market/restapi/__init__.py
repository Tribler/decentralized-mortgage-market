"""
This module contains the RESTful API for the decentralized mortgage market.
"""

from base64 import urlsafe_b64decode


def get_param(params, name):
    if name not in params or len(params[name]) == 0:
        return None
    return params[name][0]

def split_composite_key(composite_key):
    keys = composite_key.split()

    try:
        return (int(keys[0]), urlsafe_b64decode(keys[1])) if len(keys) == 2 else None
    except (TypeError, ValueError):
        return None

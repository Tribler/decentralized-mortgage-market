"""
This module contains the RESTful API for the decentralized mortgage market.
"""


def get_param(params, name):
    if name not in params or len(params[name]) == 0:
        return None
    return params[name][0]

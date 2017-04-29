"""
This package contains various models for the market api.
"""

from enum import IntEnum

class ObjectType(IntEnum):
    LOANREQUEST = 0
    MORTGAGE = 1
    INVESTMENT = 2
    TRANSACTION = 3

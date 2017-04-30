from market.dispersy.crypto import LibNaCLPK

def median(lst):
    sorted_lst = sorted(lst)
    half, odd = divmod(len(sorted_lst), 2)
    if odd:
        return sorted_lst[half]
    return (sorted_lst[half - 1] + sorted_lst[half]) / 2.

def verify_libnaclpk(key, data, signature):
    try:
        key = LibNaCLPK(key[10:])
        return key.verify(signature, data) == data
    except ValueError:
        return False

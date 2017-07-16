from market.dispersy.crypto import LibNaCLPK

def zero_pad(data, length, prepend=False):
    padding = '\x00' * (length - len(data))
    return padding + data if prepend else data + padding

def int_to_bin(i):
    hex_str = '%x' % i
    hex_str = '0' + hex_str if len(hex_str) % 2 == 1 else hex_str
    return hex_str.decode('hex')

def bin_to_int(b):
    return int(b.encode('hex'), 16)

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

from market.util.misc import bin_to_int, int_to_bin, zero_pad

def compact_to_uint256(compact):
    assert len(compact) == 4
    exp = bin_to_int(compact[0])
    binary = compact[1:exp + 1] + '\x00' * (exp - 3)
    return bin_to_int(binary)

def uint256_to_compact(uint256):
    # Note that our compact format is unsigned (unlike Bitcoin)
    assert 0 <= uint256 < 2 ** 256 - 1
    binary = int_to_bin(uint256)
    exp = max(1, len(binary))
    return zero_pad(int_to_bin(exp) + binary[:3], 4)

def full_to_uint256(full):
    assert len(full) == 32, len(full)
    return bin_to_int(full)

def uint256_to_full(uint256):
    assert 0 <= uint256 < 2 ** 256
    return zero_pad(int_to_bin(uint256), 32, prepend=True)

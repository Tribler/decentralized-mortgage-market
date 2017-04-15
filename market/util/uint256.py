def bytes_to_uint256(byte_str):
    assert len(byte_str) == 32
    return int(byte_str.encode('hex'), 16)

def uint256_to_bytes(uint256):
    assert uint256 < 2 ** 256
    return ('%064x' % uint256).decode('hex')

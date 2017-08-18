from dispersy.crypto import LibNaCLSK

NUM_RANDOM_BITS = 1024 * 8  # bits


def generate_keypair():
    return LibNaCLSK()


def read_keypair(keypairfilename):
    with open(keypairfilename, 'rb') as keyfile:
        binarykey = keyfile.read()
    return LibNaCLSK(binarykey=binarykey)


def save_keypair(keypair, keypairfilename):
    with open(keypairfilename, 'wb') as keyfile:
        keyfile.write(keypair.key.sk)
        keyfile.write(keypair.key.seed)

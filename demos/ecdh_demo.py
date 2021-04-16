import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from third_party.ecdsa import ECDH, SECP128r1, SigningKey, VerifyingKey

alice = ECDH(curve=SECP128r1)
alice.generate_private_key()
alice_compressed_public_key = alice.get_public_key().to_string("compressed")[1:]
print(f"Alice's private key: \n\t" \
    f"{alice.private_key.to_string().hex()}")
print(f"Alice's compressed pubilc key:\n\t" \
    f"length: {len(alice_compressed_public_key)}, " \
    f"public key: {alice_compressed_public_key.hex()}")

bob = ECDH(curve=SECP128r1)
bob.generate_private_key()
bob_compressed_public_key = bob.get_public_key().to_string("compressed")[1:]
print(f"Bob's private key: \n\t" \
    f"{bob.private_key.to_string().hex()}")
print(f"Bob's compressed pubilc key:\n\t" \
    f"length: {len(bob_compressed_public_key)}, " \
    f"public key: {bob_compressed_public_key.hex()}")

restored_key_alice = '02' + str(alice_compressed_public_key.hex())
restored_key_alice = VerifyingKey.from_string(bytearray.fromhex(restored_key_alice), curve=SECP128r1)

restored_key_bob = '02' + str(bob_compressed_public_key.hex())
restored_key_bob = VerifyingKey.from_string(bytearray.fromhex(restored_key_bob), curve=SECP128r1)

bob.load_received_public_key(restored_key_alice)
alice.load_received_public_key(restored_key_bob)

print("\n\n"\
    "Alice's shared secret:\n\t"\
    f"{alice.generate_sharedsecret()} \n"\
    "Bob's shared secret:\n\t"\
    f"{bob.generate_sharedsecret()}\n"
    )


from utility import *
bob = EncMgr()
alice = EncMgr()

print(f"{alice.get_shared(bob.pub_key)}, {bob.get_shared(alice.pub_key)}")



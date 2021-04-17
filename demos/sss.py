import shamir_mnemonic as shamir
import random
# original code
# def test_basic_sharing_random():
#     secret = secrets.token_bytes(16)
#     mnemonics = shamir.generate_mnemonics(1, [(3, 5)], secret)[0]
#     assert shamir.combine_mnemonics(mnemonics[:3]) == shamir.combine_mnemonics(
#         mnemonics[2:]
#     )

def create_shares(secret):
    #secret = secrets.token_bytes(16)
    secret = secret.encode('utf-8')
    shares = shamir.generate_mnemonics(1, [(3, 6)], secret)[0]
    return shares
    # assert shamir.combine_mnemonics(shares[:3]) == shamir.combine_mnemonics(
    #     shares[2:])

msg = 'ABCDGERT23456780'
shares = create_shares(msg)
print('the shares are',shares)
pool = random.sample(shares, 3)
new_msg = shamir.combine_mnemonics(pool)
pool = random.sample(shares, 2)
fakepool = [shares[1],shares[1],shares[1]]


print('shares are',shares)
print('origin msg is',msg)
print('decryted message is',new_msg.decode('utf-8'))

try:
    fake_msg = shamir.combine_mnemonics(fakepool)
    print('fake message is',fake_msg)
except:
    print('too many or not enough keys')

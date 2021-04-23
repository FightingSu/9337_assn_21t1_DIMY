
import random

from Crypto.Protocol.SecretSharing import Shamir as shamir
msg = 'ABCDGERT23456780'
msg = msg.encode('utf-8')
shares = shamir.split(3,6,msg,ssss=True)
print(shares)
pool_1 = random.sample(shares, 3)
pool_2 = random.sample(shares,2)
pool_3 = random.sample(shares,4)
tmp = []
count = 1
for i in pool_3:
    shit = (count,i[1])
    tmp.append(shit)
    count = count + 1
remake_1 = shamir.combine(pool_1)
remake_2 = shamir.combine(pool_2) 
remake_3 = shamir.combine(pool_3)
remake_4 = shamir.combine(tmp)
what = []
for i in pool_1:
    add = str(i[0]).encode('utf-8') + ' '.encode('utf-8') + i[1]
    what.append(add)

for i in what:
    # print(len(i[2:]))
    print(int(i[0:1]))

print(remake_1,remake_2)
print(type(shares[1]))
print(len(shares[1][1]))
if remake_1 == msg :
    print("Yes Yes!")
else:
    print("Oh no!")

if remake_2 == msg :
    print("Yes Yes!")
else:
    print("Oh no!")


if remake_3 == msg :
    print("Yes Yes!")
else:
    print("Oh no!")

if remake_4 == msg :
    print("Yes Yes!")
else:
    print("Oh no!")

# from the test, we know that more keys won't cause trouble
import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from utility import bloom_filter, query_contact, upload_contact
from pprint import pprint

bf = bloom_filter(800000, 3, 1000)
bf.put("amazing")
bf.put("great")

result = query_contact(bf, 'http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/qbf/query')
pprint(result)
if result.find("No Match"):
    print("result: None Match!")
result = upload_contact(bf, 'http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/cbf/upload')
pprint(result)

result = query_contact(bf, 'http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/cbf/query')
pprint(result)

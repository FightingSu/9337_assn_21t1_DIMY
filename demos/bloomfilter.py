import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from utility import bloom_filter

bf = bloom_filter(800000, 2, 1000)
bf.put("amazing")
bf.put("great")

has_get = bf.get("amazing")
has_great = bf.get("great")
has_fun = bf.get("fun")
print(f"Check get: {has_get}\ncheck great: {has_great}\ncheck fun: {has_fun}")
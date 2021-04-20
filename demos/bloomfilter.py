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


b1 = bloom_filter(4, 2, 2)
b2 = bloom_filter(4, 2, 2)
print(b1.bitarr)
print(b2.bitarr)

insert_pos1 = b1.put("233")
insert_pos2 = b2.put("122")
print(f"Insert position of b1: {insert_pos1}\nInsert position of b2: {insert_pos2}")
print(b1.bitarr)
print(b2.bitarr)

print(bloom_filter.combine_filters([b1, b2]).bitarr)

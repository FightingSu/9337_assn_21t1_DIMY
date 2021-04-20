import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from third_party.pymmh3 import hash as murmur32

hash_val = murmur32('02dfa1281937981232112389712934691823764918726349187236123874619287365102973645912873649187235468172534123984601827364912343adf1232', 
                    seed=1234)
hash_val_bytearr = hash_val.to_bytes(4, sys.byteorder, signed=True)
print(f"hash value is {hash_val_bytearr}\nlength is {len(hash_val_bytearr)}")
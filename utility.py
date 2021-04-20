# library for ECDH
from third_party.ecdsa import ECDH, SECP128r1, VerifyingKey

# library for generating murmur hash
from third_party.pymmh3 import hash as mmhash32

# bitarray, used in bloom_filter
from bitarray import bitarray

# random number
from random import randint

# network related libraries
import socket
import requests
from requests.exceptions import Timeout
import json
from base64 import b64encode

# multi-thread related
from time import sleep
from threading import Thread

# sss
from third_party.sss import create_shares, combine_shares

# default list
from collections import defaultdict

# use sys.byteorder
import sys

def query_contact (QBF, url):
    data = json.dumps({"QBF": "{}".format(b64encode(QBF.bitarr.tobytes()))})
    headers={"Content-Type":"application/json"}
    try:
        response = requests.post(url, data=data, headers=headers)
    except Timeout:
        print("----- Timeout error, retrying... -----")
        return ''
    else:
        return response.text

def upload_contact (CBF, url):
    data = json.dumps({"CBF": "{}".format(b64encode(CBF.bitarr.tobytes()))})
    headers={"Content-Type":"application/json"}
    try:
        response = requests.post(url, data=data, headers=headers)
    except Timeout:
        print("----- Timeout error, retrying... -----")
        return ''
    else:
        return response.text

# used when debugging
def bytearr_hex_to_str(bytearr_key: bytearray):
    return bytearr_key.hex()

# used when debugging
def str_hex_to_bytearr(str_key: str):
    return bytearray.fromhex(str_key)

# generate murmur hash in 3 bytes
def generate_identifier(pub_key: bytearray):
    hash_val = mmhash32(pub_key, seed=randint(0, 100000000))
    hash_val_bytearr = hash_val.to_bytes(4, sys.byteorder, signed=True)[:3]
    return hash_val_bytearr


class bloom_filter(object):
    # m is the size of the filter
    # k is the number of hashes
    # n is the number of entries to be stored
    def __init__(self, m, k, n):
        self.filter_size = m
        self.num_hashes = k
        self.num_entries = n
        self.bitarr = bitarray(self.filter_size)
        self.bitarr.setall(0)
    
    def put(self, item):
        pos = []
        for i in range(0, self.num_hashes):
            map_to = mmhash32(item, i + 2048) % self.filter_size
            self.bitarr[map_to] = True
            pos.append(map_to)
        return pos
    
    def get(self, item):
        for i in range(0, self.num_hashes):
            map_to = mmhash32(item, i + 2048) % self.filter_size
            if self.bitarr[map_to] == False:
                return False
            
        return True

    @staticmethod
    def combine_filters(filters: list):
        bf = bloom_filter(filters[0].filter_size, filters[0].num_hashes, filters[0].num_entries)
        for f in filters:
            bf.bitarr |= f.bitarr
        return bf
        

'''
A simple recource manager managing the
generation of ephid and encid.
'''
class enc_mgr(object):
    def __init__(self):
        self.mgr = ECDH(curve=SECP128r1)
        self.mgr.generate_private_key()
        self.priv_key = self.mgr.private_key.to_string()
        self.pub_key = self.mgr.get_public_key().to_string("compressed")[1:]
        self.mmh32 = generate_identifier(self.pub_key)
    
    #EchID
    def get_shared(self, pub_key: str):
        restored_key = bytearray.fromhex('02') + pub_key
        restored_key = VerifyingKey.from_string(restored_key, curve=SECP128r1)
        self.mgr.load_received_public_key(restored_key)
        hex_encid = hex(self.mgr.generate_sharedsecret())[2:]
        prefix = "0" * (32 - len(hex_encid))
        hex_encid = prefix + hex_encid
        return bytearray.fromhex(hex_encid)

    def new_priv_key(self):
        self.mgr.generate_private_key()
        self.priv_key = self.mgr.private_key.to_string()
        self.pub_key = self.mgr.get_public_key().to_string("compressed")[1:]
        self.mmh32 = generate_identifier(self.pub_key)



'''
Object that sends out ephid and receive from others.
'''
class client(object):
    def __init__(self, port):
        # broadcasting port
        self.port = port

        # encounter id manager
        self.encmgr = enc_mgr()

        # ephid broadcast count
        # if one ephid broadcasted many times
        # generate a new one instead
        # (use enc_mgr.new_priv_key())
        # and reset ephid_cnt
        self.ephid_cnt = 0

        # fragments generated by shamir's secret sharing
        # for broadcasting
        self.msg = create_shares(self.encmgr.pub_key)

        # broadcasting thread
        self.broadcast_thread = Thread(target=self.send)

        # listening thread
        self.monitor_thread = Thread(target=self.listen)
        # key is hash of ephid received, NOT IP ADDRESS
        # value is the fragment of ephid
        #
        # it shall looks like:
        # { 
        #     "2efda":
        #     {
        #         1: "23abd2fda",
        #         2: "1092fdace",
        #     }
        # }
        # 
        # when complete ephid received, restore ephid and
        # move it in self.ephid_complete
        self.ephid_frag = defaultdict(list)

        # complete ephids
        self.ephid_complete = defaultdict(list)

        # create a bloom filter
        self.DBFs = bloom_filter(800000,2,1000)
        self.DBFs_list = []


    # start broadcasting and monitoring
    def start_service(self):
        self.broadcast_thread.start()
        self.monitor_thread.start()

    # listen to others' broadcast
    # the listen function should perform shamir's secret sharing
    # we use self.ephid_complete_check() to perform such operation
    # and tries to restort ephid from fragments received
    # the hashid can't be decoded by utf-8, so when a message is recieved
    # kick out the hashid from the end of the message. Hashid's length is 3 byte
    def listen(self):
        print("function 'listen' not finished!")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', self.port))
        print(f"Listening for broadcast at {s.getsockname()}")
        while True:
            data, address = s.recvfrom(1024)
            recived_hashid = data[-3:]
            data = data[0:-4]
            # print('Server received from {}: {}'.format(address, data.decode('utf-8')))
            print('the message I recieved:\n',data)
            self.ephid_complete_check(data.decode('utf-8'),recived_hashid)
        
    # broadcast
    # the send function should generate new ephid when needed
    # we use self.ephid_cnt_check() function to check whether a new 
    # ephid should be generated
    def send(self):
        print("function 'send' not finished!")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        network = '<broadcast>'
        # hashid = self.encmgr.mmh32
        while(True):
            share_hash = self.msg.pop().encode('utf-8') + ' '.encode('utf-8') + self.encmgr.mmh32 
            print('the message I send:\n',share_hash)
            print(self.encmgr.mmh32)
            s.sendto(share_hash, (network, self.port))
            print("----------sending EphID----------")
            self.ephid_cnt_check()
            sleep(1)

    def ephid_cnt_check(self):
    #    print("function 'ephid_cnt_check' not finished!")
        self.ephid_cnt = self.ephid_cnt + 1
        print("{} messages have been sent".format(self.ephid_cnt))
        #for every 10 minutes, a new bloom filter will be created
        if (self.ephid_cnt % 600 ==0):
            print("It's 10 minutes, generate a new daily bloom filter!")
            self.DBFs_list.append(self.DBFs)
            self.DBFs = bloom_filter(800000,2,1000)

        if (self.ephid_cnt % 6 == 0 ):
            self.encmgr.new_priv_key()
            # self.ephid_cnt = 0
            self.msg = create_shares(self.encmgr.pub_key)
            self.encmgr.mmh32 = self.encmgr.mmh32
            print('Generate new ID') 

        # if one hour later, the first element in DBFs_list will be deleted
        if (len(self.DBFs_list) == 6):
            self.DBFs_list.pop(0)




    def ephid_complete_check(self, fragments,hashid):
        # print("function 'ephid_complete_check' not finished!")
        # the key is app's hashid and value is the sare messages.
        # Once get 3 or more than 3 messages from a same hashid, decode its EphID.
        # And then move this EphId into ephid_complete
        # delete this id from the this dictionary
        self.ephid_frag[hashid].append(fragments)
        completed = []
        for i in  self.ephid_frag:
            if len(set(self.ephid_frag[i])) >= 3:
                print('get enough shares, start to decode the ephid')
                print("generate the EncID using EphID")
                true_id = combine_shares(self.ephid_frag[i][0:3])
                encid = self.encmgr.get_shared(true_id)
                self.DBFs.put(encid)
                # if (true_id == self.encmgr.pub_key):
                #     print('oh yeah!!!')
                self.ephid_complete[len(self.ephid_complete) + 1].append(true_id)
                completed.append(i)
        # delete the hashid from this dictionary
        for i in completed:
            del self.ephid_frag[i]
                
            





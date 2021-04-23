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
# from third_party.sss import create_shares, combine_shares
from Crypto.Protocol.SecretSharing import Shamir as shamir

# default list
from collections import defaultdict

# use sys.byteorder
import sys

# import for the backend server
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from pprint import pprint

# import datetime to calculate time
import datetime

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
    hash_val = mmhash32(pub_key, seed=233)
    hash_val_bytearr = hash_val.to_bytes(4, sys.byteorder, signed=True)[:3]
    return hash_val_bytearr


def count_time():
    today = datetime.datetime.now()
    add = datetime.timedelta(hours=0.5)
    new_time = (today + add).strftime('%Y-%m-%d %H:%M:%S')
    return today,new_time



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
        self.mmh32 = generate_identifier(self.pub_key)  # the hash value
    
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
        # self.ephid_cnt is set to a value very close to 3600(1 hours)
        # based on the output format of txt
        # to meet the standard output, a QBF should be created
        # after sending three messages
        self.ephid_cnt = 354

        # fragments generated by shamir's secret sharing
        # for broadcasting
        #self.msg = shamir.split(self.encmgr.pub_key)
        self.msg = self.change_format()
        # broadcasting thread
        self.broadcast_thread = Thread(target=self.send)

        # listening thread
        self.monitor_thread = Thread(target=self.listen)

        # backend communicate thread
        # QBF will be sent to the backend server, and get the result
        self.backend_thread = Thread(target=self.backend_communication)
        self.CBF_upload = Thread(target= self.upload_CBF)
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

        # a list which will record the user's own hashid
        # only contain the newest 2 ids
        self.my_hash_id = []
        
        
        # stored positions for QBFs

        # create a bloom filter
        
        self.DBFs = bloom_filter(800000,3,1000)
        print(">>>>> Service start working, client is working on UDP port {} <<<<<\n".format(self.port))
        print("======= create a new Contact BloomFilter (every 10 minutes will create a new one, maximum 6 CBFs) ======= \n")
        self.DBFs_list = []
        

    
    # start broadcasting and monitoring
    def start_service(self):
        
        self.broadcast_thread.start()
        self.monitor_thread.start()
        self.backend_thread.start()
        self.CBF_upload.start()
        

    # listen to others' broadcast
    # the listen function should perform shamir's secret sharing
    # we use self.ephid_complete_check() to perform such operation
    # and tries to restort ephid from fragments received
    # the hashid can't be decoded by utf-8, so when a message is recieved
    # kick out the hashid from the end of the message. Hashid's length is 3 byte
    def listen(self):
        #print("function 'listen' not finished!")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', self.port))
        # print(f"Listening for broadcast at {s.getsockname()}")
        # the hash_id_list is created to avoid recieving user's own id
        # when six shares are sent, new hash is generated, while the reciever
        # recieves the old id( listhen and send does not happen at the same time) 
        while True:
            data, address = s.recvfrom(1024)
            recived_hashid = data[-3:]
        
            if recived_hashid in self.my_hash_id:
                continue

            # print('Server received from {}: {}'.format(address, data.decode('utf-8')))
            print('[Segment 3-B, received share: {}]'.format(data[2:-4].hex()))
            # print('Segment 3-B, received share: {}'.format(data))
            data = data[0:-4]
            self.ephid_complete_check(data,recived_hashid)
        
    # broadcast
    # the send function should generate new ephid when needed
    # we use self.ephid_cnt_check() function to check whether a new 
    # ephid should be generated
    def send(self):
        # print("function 'send' not finished!")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        network = '<broadcast>'
        # hashid = self.encmgr.mmh32
        while(True):
            # print the values
            
            if(len(self.msg) == 6):
                print("------------------> Segment 1 <------------------")
                print("[ generate EphID:{}]".format(self.encmgr.pub_key.hex()))
                print("[ hash value of EphID: {}]\n".format(self.encmgr.mmh32.hex()))
                print("------------------> Segment 2 <------------------")
                print("Six Shares:")
                for i in self.msg:
                    print(i[2:].hex())
            
            # every time sending a message, add own hash_id into the list
            if len(self.my_hash_id)==2 :
                self.my_hash_id.pop(0)
            self.my_hash_id.append(self.encmgr.mmh32)

            share_hash = self.msg.pop() + ' '.encode('utf-8') + self.encmgr.mmh32
            print("------------------> Segment 3 <------------------\n")
            print('[Segment 3-A, sending share: {}]\n'.format(share_hash[2:-4].hex()))
            # print('[Segment 3-A, sending share: {}]\n'.format(share_hash))
            # print(self.encmgr.mmh32)
            s.sendto(share_hash, (network,self.port))
            self.ephid_cnt_check()
            sleep(5)
    
    def backend_communication(self):
        while(True):
            # 10*360 = 3600 , 1 hour
            if( self.ephid_cnt == 360):
                # sleep 5 is very important
                # As when self.ephid_cnt = 360, the bloomfilter may have not
                # appended to the list, and this thread starts and begin to combine the filters
                # every one hour combine six filters into one
                now,nowplus = count_time()
                if len(self.DBFs_list)>= 1:
                    six_filters = bloom_filter.combine_filters(self.DBFs_list)
                    print("------------------> Segment 8 <------------------\n")
                    print("[combine DBFs into a single QBF - {}]".format(now))
                    print("[ Currently have {} DBF, the state:".format(len(self.DBFs_list)))
                    for i in self.DBFs_list:
                        tmp = self.find_position(i)
                        if len(tmp) != 0:
                            print(tmp)
                        else:
                            print("empty")
                    print("[ Single QBF: {} ]".format(self.find_position(six_filters)))
                    print("[ NEXT QUERY TIME - {} ]".format(nowplus))
                    print("uploading QBF to backend server...")
                    result = query_contact(six_filters, 'http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/qbf/query')
                    if result.find("No Match"):
                        print("------------------> Segment 8 <------------------\n")
                        print("result: None Match!")
                    else:
                        print("------------------> Segment 8 <------------------\n")
                        print("you may get infected because you contact with dangerous person!")
                    result = upload_contact(six_filters, 'http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/cbf/upload')

                    # once a QBF is uploaded, we can delete the six DBFs
                    del six_filters
                else:
                    print("No DBF, can't combine filter!")
    
    
    
    # find what position in the filter is 1
    def find_position(self,BF):
        pos = []
        tmp = str(BF.bitarr)[10:-2]
        for i in range(0,len(tmp)):
            if tmp[i] == "1":
                pos.append(i)
        return pos
    
    # get normal shares
    def change_format(self):
        msg = []
        tmp = shamir.split(3,6,self.encmgr.pub_key)
        for i in tmp:
            add = str(i[0]).encode('utf-8') + ' '.encode('utf-8') + i[1]
            msg.append(add)
        return msg
    
    def decode_ephid(self,items):
        # print(type(items))
        tmp = []
        for i in items:
            num = int(i[0:1])
            words = i[2:]
            tmp.append((num,words))
        id = shamir.combine(tmp)
        return id

        #shamir.combine(self.ephid_frag[i][0:3])




        




    def ephid_cnt_check(self):
    #    print("function 'ephid_cnt_check' not finished!")
        self.ephid_cnt = self.ephid_cnt + 1
        # print("{} messages have been sent".format(self.ephid_cnt))

        #for every 10 minutes, a new bloom filter will be created
        # 60
        if (self.ephid_cnt % 30 ==0):
            # print("It's 2.5 minutes, generate a new daily bloom filter!")
            self.DBFs_list.append(self.DBFs)
            self.DBFs = bloom_filter(800000,3,1000)
            print("======= create a new Contact BloomFilter (every 10 minutes will create a new one, maximum 6 CBFs) ======= \n")
            # every 10 minutes, clear the contact list
            # for i in self.ephid_frag:
            #     if len(self.ephid_frag[i]) <=1:

            # dict.clear(self.ephid_frag)

        # after every 6 sendings (1 minute) change a new EphID
        if (self.ephid_cnt % 6 == 0 ):
            self.encmgr.new_priv_key()
            # self.ephid_cnt = 0
            self.msg = self.change_format()
            # self.encmgr.mmh32 = self.encmgr.mmh32
            # print('Generate new ID') 

        # if one hour passes, the first element in DBFs_list will be deleted
        if (len(self.DBFs_list) == 7):
            deleted_bloom = self.DBFs_list.pop(0)
            del deleted_bloom
        
        # every 5 minutes upload the 6 bloom filters
        if (self.ephid_cnt == 60):
            self.ephid_cnt = 0




    def ephid_complete_check(self, fragments,hashid):
        # print("function 'ephid_complete_check' not finished!")
        # the key is app's hashid and value is the sare messages.
        # Once get 3 or more than 3 messages from a same hashid, decode its EphID.
        # And then move this EphId into ephid_complete
        # delete this id from the this dictionary
        self.ephid_frag[hashid].append(fragments)
        completed = []

        # print how many shares are recieved

        tmp = 0
        for i in  self.ephid_frag:
            tmp = tmp + len(self.ephid_frag[i])
        print("[Segment 3-C, total shares received: {}]".format(tmp))
        # tmp = self.ephid_frag[-1]
        # print("Segment 3-C, total shares received: {}".format(len(tmp)))


        for i in  self.ephid_frag:
            if len(set(self.ephid_frag[i])) >= 3:
                print("------------------> Segment 4 <------------------\n")
                # decode the EphID 
                true_id = self.decode_ephid(self.ephid_frag[i])
                print("Segment 4-A, re-construct EphID: {}".format(true_id.hex()))
                # print("Segment 4-A, re-construct EphID: {}".format(true_id))
                r_hashid = generate_identifier(true_id)
                print("Segment 4-B, hash value of re-constructed EphID: {} is equal to hash value of original EphID: {}".format(r_hashid.hex(),hashid.hex()))


                #generate the EncID
                encid = self.encmgr.get_shared(true_id)
                print("------------------> Segment 5 <------------------\n")
                print("[generate shared secret EncID: {}]".format(encid.hex()))

                # put the EncID into the bloom filter then delete the EncID
                print("======== insert into DBF (murmur3 hashing with 3 hashes) ========\n")
                positions = self.DBFs.put(encid)
                print("Segment 7-A, insert EncID into DBF at positions:",positions)
                positions = self.find_position(self.DBFs)
                print("current DBF state after inserting new EncID: ",positions)
                del encid
                
                self.ephid_complete[len(self.ephid_complete) + 1].append(true_id)
                completed.append(i)
        
        # delete the hashid from this dictionary
        # array completed contain all the decoded EphID
        for i in completed:
            del self.ephid_frag[i]
    
    def upload_CBF(self):
        while(True):
            command = input()
            if command == None:
                continue
            if command == "uploadCBF":
                if len(self.DBFs_list) > 0:
                    six_filters = bloom_filter.combine_filters(self.DBFs_list)
                    print("------------------> Segment 10 <------------------\n")
                    print(" uploading CBF to backend server...")
                    result = upload_contact(six_filters, 'http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/cbf/upload')
                    if result.find("upload CBF success"):
                        print("------------------> Segment 10 <------------------\n")
                        print("upload CBF success")
                    else:
                        print("------------------> Segment 10 <------------------\n")
                        print("upload failed")
                else:
                    print("don't have enough DBF,need at least one DBF")
            else:
                print("Please enter: 'uploadCBF' if you are diagnosed positive with COVID-19!")

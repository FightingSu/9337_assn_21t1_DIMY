# library for ECDH
from third_party.ecdsa import ECDH, SECP128r1, VerifyingKey

# network related libraries
import socket
from time import sleep
from threading import Thread

'''
A simple recource manager managing the
generation of ephid and encid.
'''
class EncMgr(object):
    def __init__(self):
        self.mgr = ECDH(curve=SECP128r1)
        self.mgr.generate_private_key()
        self.priv_key = self.__cvt_to_str(self.mgr.private_key.to_string())
        self.pub_key = self.__cvt_to_str(
            self.mgr.get_public_key().to_string(
                "compressed")[1:]
            )
    
    def get_shared(self, pub_key: str):
        restored_key = '02' + pub_key
        restored_key = self.__cvt_to_bytearr(restored_key)
        restored_key = VerifyingKey.from_string(restored_key, curve=SECP128r1)
        self.mgr.load_received_public_key(restored_key)
        return hex(self.mgr.generate_sharedsecret())

    def new_priv_key(self):
        self.mgr.generate_private_key()
        self.priv_key = self.__cvt_to_str(self.mgr.private_key.to_string())
        self.pub_key = self.__cvt_to_str(
            self.mgr.get_public_key().to_string(
                "compressed")[1:]
            )

    @staticmethod
    def __cvt_to_str(bytearr_key: bytearray):
        return bytearr_key.hex()

    @staticmethod
    def __cvt_to_bytearr(str_key: str):
        return bytearray.fromhex(str_key)


'''
Object that sends out ephid and receive from others.
'''
class client(object):
    def __init__(self, port):
        # broadcasting port
        self.port = port

        # encounter id manager
        self.encmgr = EncMgr()

        # ephid broadcast count
        # if one ephid broadcasted many times
        # generate a new one instead
        # (use EncMgr.new_priv_key())
        # and reset ephid_cnt
        self.ephid_cnt = 0

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
        self.ephid_frag = {}

        # complete ephids
        self.ephid_complete = {}


    # start broadcasting and monitoring
    def start_service(self):
        self.msg = self.encmgr.pub_key
        self.broadcast_thread.start()
        self.monitor_thread.start()

    # listen to others' broadcast
    # the listen function should perform shamir's secret sharing
    # we use self.ephid_complete_check() to perform such operation
    # and tries to restort ephid from fragments received
    def listen(self):
        print("function 'listen' not finished!")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', self.port))
        print(f"Listening for broadcast at {s.getsockname()}")
        while True:
            data, address = s.recvfrom(1024)
            self.ephid_complete_check(data.decode('utf-8'))
            print('Server received from {}: {}'.format(address, data.decode('utf-8')))
        
    # broadcast
    # the send function should generate new ephid when needed
    # we use self.ephid_cnt_check() function to check whether a new 
    # ephid should be generated
    def send(self):
        print("function 'send' not finished!")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        network = '<broadcast>'
        while(True):
            s.sendto(self.msg.encode('utf-8'), (network, self.port))
            print("sending EphID")
            self.ephid_cnt_check()
            sleep(5)

    def ephid_cnt_check(self):
        print("function 'ephid_cnt_check' not finished!")

    def ephid_complete_check(self, fragments):
        print("function 'ephid_complete_check' not finished!")



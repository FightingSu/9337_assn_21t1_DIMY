import socket
import time
import threading

port = 7777

def send():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    network = '<broadcast>'
    while(1):
        s.sendto('你在说什么鸟语!'.encode('utf-8'), (network, port))
        print("sending message")
        time.sleep(5)


def listen():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.bind(('', port))
    print('Listening for broadcast at ', s.getsockname())
    while True:
        data, address = s.recvfrom(1024)
        print('Server received from {}:{}'.format(address, data.decode('utf-8')))

try:
    t1 = threading.Thread(target=send)
    t2 = threading.Thread(target=listen)
    t1.start()
    t2.start()
except:
    print('can not create or start the thread')




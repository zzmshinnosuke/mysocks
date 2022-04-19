SERVER = '127.0.0.1'
REMOTE_PORT = 8499
PORT = 1080
KEY = "foobar!"

import socket
import select
import string
import struct
import hashlib
import threading
import time
import socketserver

# def get_table(key):
#     m = hashlib.md5()
#     m.update(key.encode('utf-8'))
#     s = m.digest()
#     (a, b) = struct.unpack('<QQ', s)
#     table = [c for c in string.maketrans('', '')]
#     for i in range(1, 1024):
#         table.sort( lambda x, y: int(a % (ord(x) + i) - a % (ord(y) + i)))
#     return table

# encrypt_table = ''.join(get_table(KEY))
# decrypt_table = string.maketrans(encrypt_table, string.maketrans('', ''))

k = ''.join([chr(c) for c in range(256)])
v = ''.join([chr(c) for c in range(256)][::-1])
encrypt_table = str.maketrans(k, v)
decrypt_table = str.maketrans(v, k)

my_lock = threading.Lock()

def lock_print(msg):
    my_lock.acquire()
    try:
        print("[%s] %s" % (time.ctime(), msg))
    finally:
        my_lock.release()

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class Socks5Server(socketserver.StreamRequestHandler):
#     def b2s(self, data):
#         return str(data, encoding='utf-8') 
    
#     def s2b(self, data):
#         return data.encode()
    
    def encrypt(self, data):
        return data #.translate(encrypt_table)

    def decrypt(self, data):
        return data #.translate(decrypt_table)

    def handle_tcp(self, sock, remote):
        try:
            fdset = [sock, remote]
            counter = 0
            while True:
                r, w, e = select.select(fdset, [], [])
                if sock in r:
                    r_data = sock.recv(4096)
                    if counter == 1:
                        try:
                            lock_print("Connecting "+ str(r_data[5:5 + r_data[4]], "utf-8"))
                        except Exception as e:
                            pass
                    if counter < 2:
                        counter += 1
                    if remote.send(self.encrypt(r_data)) <= 0: 
                        break
                if remote in r:
                    if sock.send(self.decrypt(remote.recv(4096))) <= 0:
                        break
        finally:
            remote.close()

    def handle(self):
        try:
            sock = self.request
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((SERVER, REMOTE_PORT))
            self.handle_tcp(sock, remote)
        except socket.error as e:
            lock_print('socket error: ' + str(e))

def main():
    print('Starting proxy at port %d' % PORT)
    server = ThreadingTCPServer(('', PORT), Socks5Server)
    server.serve_forever()

if __name__ == '__main__':
    main()
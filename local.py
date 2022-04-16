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
import SocketServer

def get_table(key):
    m = hashlib.md5()
    m.update(key)
    s = m.digest()
    (a, b) = struct.unpack('<QQ', s)
    table = [c for c in string.maketrans('', '')]
    for i in xrange(1, 1024):
        table.sort(lambda x, y: int(a % (ord(x) + i) - a % (ord(y) + i)))
    return table

encrypt_table = ''.join(get_table(KEY))
decrypt_table = string.maketrans(encrypt_table, string.maketrans('', ''))

my_lock = threading.Lock()

def lock_print(msg):
    my_lock.acquire()
    try:
        print "[%s]%s" % (time.ctime(), msg)
    finally:
        my_lock.release()


class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class Socks5Server(SocketServer.StreamRequestHandler):
    def encrypt(self, data):
        return data.translate(encrypt_table)

    def decrypt(self, data):
        return data.translate(decrypt_table)

    def handle_tcp(self, sock, remote):
        fdset = [sock, remote]
        counter = 0
        while True:
            r, w, e = select.select(fdset, [], [])
            if sock in r:
                r_data = sock.recv(4096)
                if counter == 1:
                    try:
                        lock_print("Connecting " + r_data[5:5 + ord(r_data[4])])
                    except Exception:
                        pass
                if counter < 2:
                    counter += 1
                if remote.send(self.encrypt(r_data)) <= 0: break
            if remote in r:
                if sock.send(self.decrypt(remote.recv(4096))) <= 0:
                    break

    def handle(self):
        try:
            sock = self.connection
            remote = socket.socket()
            remote.connect((SERVER, REMOTE_PORT))
            self.handle_tcp(sock, remote)
        except socket.error as e:
            lock_print(e)


def main():
    print 'Starting proxy at port %d' % PORT
    server = ThreadingTCPServer(('', PORT), Socks5Server)
    server.serve_forever()

if __name__ == '__main__':
    main()
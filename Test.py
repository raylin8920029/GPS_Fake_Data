from multiprocessing.reduction import ForkingPickler
import StringIO

def forking_dumps(obj):
    buf = StringIO.StringIO()
    ForkingPickler(buf).dump(obj)
    return buf.getvalue()

from multiprocessing import Queue, Process
from socket import socket
import pickle

def handle(q):
    sock = pickle.loads(q.get())
    print 'rest:', sock.recv(2048)

if __name__ == '__main__':
    sock = socket()
    sock.connect(('httpbin.org', 80))
    sock.send(b'GET /get\r\n')
    # first bytes read in parent
    print 'first part:', sock.recv(50)

    q = Queue()
    proc = Process(target=handle, args=(q,))
    proc.start()
    # use the function from above to serialize socket
    q.put(forking_dumps(sock))
    proc.join()
import sys
from socketTCP import SocketTCP

socket = SocketTCP()

addr = sys.argv[1]
port = sys.argv[2]
mssg = sys.stdin.buffer.read()


address = (addr, int(port))


socket.connect(address)


socket.send(mssg)

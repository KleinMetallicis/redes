import sys
from socketTCP import SocketTCP

socket = SocketTCP()

addr = sys.argv[1]
port = sys.argv[2]

address = (addr, int(port))


mssg = input()
print(mssg)

socket.connect(address)


socket.send(mssg)

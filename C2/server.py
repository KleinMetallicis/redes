from socketTCP import SocketTCP

socket = SocketTCP()

address = ('localhost', 8000)
socket.bind(address)

socket.accept()


rcv = socket.recv(16)

print(rcv)

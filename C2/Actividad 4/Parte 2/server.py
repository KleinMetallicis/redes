from socketTCP import SocketTCP

socket = SocketTCP()

address = ('localhost', 8000)
socket.bind(address)



listener_data = socket.accept()
listener = listener_data[0]

rcv = listener.recv(16, "go_back_n")

print(rcv)

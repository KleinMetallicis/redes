import socket, random

BUFF_SIZE = 16
TIMEOUT = 2

class SocketTCP:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(TIMEOUT)
        self.address = None
        self.destiny = None
        self.seq = 0
        self.expected_seq = 0

    def parse_segment(self, segment: bytes):
        segment_list = segment.split(b'|||')
        
        headers = [bool(int(x)) for x in segment_list[:3]]
        headers.append(int(segment_list[3]))
        data = b''
        try:
            data = segment_list[4]
        except:
            pass
        syn, ack, fin, seq = headers
        return (syn, ack, fin, seq, data)

    def create_segment(self, tuple):
        data_list = str(tuple[0]).encode()
        for i in tuple[1:4]:
            data_list += b'|||' + str(i).encode()
        
        data_list += b'|||' + tuple[4]
        
        return data_list

    def bind(self, address):
        self.address = address
        self.socket.bind(self.address)
    
    def connect(self, destiny):
        self.seq = random.randint(0,100)
        self.expected_seq = self.seq
        self.destiny = destiny
        while True:
            try:
                syn_segment = self.create_segment((1, 0, 0, self.seq, b''))
                self.socket.sendto(syn_segment, destiny)
                while True:
                    data, addr = self.socket.recvfrom(1024) 
                    self.destiny = addr
                    syn, ack, _, seq, _ = self.parse_segment(data)
                    if syn and ack and (seq == self.expected_seq):
                        self.seq += 1
                        self.expected_seq +=1
                        ack_seg = self.create_segment((0, 1, 0, self.seq, b''))
                        self.socket.sendto(ack_seg, self.destiny)
                        break
                self.seq +=1
                self.expected_seq +=1
                break
            except socket.timeout:
                print("timeout")
                continue

    def accept(self):
        while True:
            try:
                data, address = self.socket.recvfrom(1024)
                syn, ack, fin, seq, body = self.parse_segment(data)
                
                if syn and not ack:
                    new_socket = SocketTCP()
                    new_socket.address = (self.address[0], self.address[1] + 1)
                    new_socket.destiny = address
                    new_socket.bind(new_socket.address)
                    new_socket.seq = seq
                    new_socket.expected_seq = seq + 1
                    syn_ack_seg = new_socket.create_segment((1, 1, 0, new_socket.seq, b''))
                    
                    new_socket.socket.sendto(syn_ack_seg, address)
                    
                    while True:
                        data, addr = new_socket.socket.recvfrom(1024)
                        syn2, ack2, fin2, seq2, body2 = new_socket.parse_segment(data)
                        if ack2 and not syn2 and addr == address and seq2 == new_socket.expected_seq:

                            new_socket.seq = seq2
                            new_socket.expected_seq = seq2 + 1
                            print("Connection accepted from " + str(address))
                            break
                            
                    return new_socket, new_socket.address

            except socket.timeout:
                continue

    def send(self, message):
        out = message
        message_length = len(out)
        data_list = []
        while out:
            data_list.append(out[:BUFF_SIZE])
            out = out[BUFF_SIZE:]

        data_list = [str(message_length).encode()] + data_list
        
        while data_list:
            try:
                out_mssg = data_list[0]
                out_seg = self.create_segment((0, 0, 0, self.seq, out_mssg))
                self.socket.sendto(out_seg, self.destiny)
                data, addr = self.socket.recvfrom(1024)
                syn, ack, fin, seq, _ = self.parse_segment(data)
                if ack and (seq == self.expected_seq):
                    data_list = data_list[1:]
                    self.expected_seq += 1
                    self.seq += 1
                    tries = 0
                else:
                    continue

            except socket.timeout:
                continue

    def recv(self, buff_size):
        head_length = len(b'0|||0|||0||||||') 
        calc_buffer = head_length + buff_size 
        while True:
            try:
                data, addr = self.socket.recvfrom(calc_buffer + len(str(self.expected_seq).encode()))
                syn, ack, fin, seq, message_length = self.parse_segment(data)
                
                if seq == self.expected_seq:
                    first_ack = self.create_segment((0,1,0, seq, b''))
                    self.socket.sendto(first_ack, addr)
                    self.seq += 1
                    self.expected_seq +=1
                    break
                    
            except:
                continue
                
        remaining_message = int(message_length)
        message = b''
        while remaining_message:
            try:
                if remaining_message > buff_size:
                
                    data, addr = self.socket.recvfrom(calc_buffer + len(str(self.expected_seq).encode()))
                    _,_,_, seq, body = self.parse_segment(data)
                    if self.expected_seq == seq:
                        message += body
                        ack_seg = self.create_segment((0,1,0,seq,b''))
                        self.socket.sendto(ack_seg, addr)
                        self.seq +=1
                        self.expected_seq += 1
                        remaining_message -= buff_size
                    elif self.expected_seq > seq:
                        ack_seg = self.create_segment((0,1,0,seq, b''))
                        self.socket.sendto(ack_seg, addr)

                    else:
                        continue
                
                else:
                    data, addr = self.socket.recvfrom(head_length + remaining_message + len(str(self.expected_seq)))
                    _,_,_, seq, body = self.parse_segment(data)
                    if self.expected_seq == seq:
                        message += body
                        ack_seg = self.create_segment((0,1,0,seq, b''))
                        self.socket.sendto(ack_seg, addr)
                        self.seq += 1
                        self.expected_seq += 1 
                        remaining_message -= remaining_message
                    
                    elif self.expected_seq > seq:
                        ack_seg = self.create_segment((0,1,0,seq, b''))
                        self.socket.sendto(ack_seg, addr)
                    
                    else:
                        continue
            except socket.timeout:
                continue

        return message
    
    def close(self):
        pass
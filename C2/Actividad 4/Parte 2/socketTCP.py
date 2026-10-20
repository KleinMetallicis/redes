import socket, random, slidingWindowCC
from socketUDP import SocketUDP
BUFF_SIZE = 16
TIMEOUT = 2
WINDOW_SIZE = 8

class SocketTCP(SocketUDP):
    def __init__(self):
        super().__init__()
        self.socket = self.socket_udp
        self.socket.settimeout(TIMEOUT)
        self.settimeout(TIMEOUT)
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
        segment = b'|||'.join([bytes(int(element)) for element in tuple[:4]]) + b'|||' + tuple[4]
        
        return segment

    def bind(self, address):
        self.address = address
        self.socket.bind(self.address)
    
    def connect(self, destiny):
        self.seq = random.randint(0,100)
        self.expected_seq = self.seq
        self.destiny = destiny
        while True:
            try:
                syn_segment = self.create_segment((1, 0, 0, self.seq, ''))
                self.socket.sendto(syn_segment, destiny)
                while True:
                    data, addr = self.socket.recvfrom(1024) 
                    self.destiny = addr
                    syn, ack, _, seq, _ = self.parse_segment(data)
                    if syn and ack and (seq == self.expected_seq):
                        self.seq += 1
                        self.expected_seq +=1
                        ack_seg = self.create_segment((0, 1, 0, self.seq, ''))
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
                    syn_ack_seg = new_socket.create_segment((1, 1, 0, new_socket.seq, ''))
                    
                    new_socket.socket.sendto(syn_ack_seg, address)
                    
                    while True:
                        data, addr = new_socket.socket.recvfrom(1024)
                        syn2, ack2, fin2, seq2, body2 = new_socket.parse_segment(data)
                        if ack2 and not syn2 and addr == address and seq2 == new_socket.expected_seq:

                            new_socket.seq = seq2
                            new_socket.expected_seq = new_socket.seq + 1
                            print("Connection accepted from " + str(address))
                            return new_socket, new_socket.address
            except socket.timeout:
                continue

    def send(self, message, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        if mode == "go_back_n":
            self.send_using_go_back_n(message)
    
    def recv(self, buff_size, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        if mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

    def send_using_stop_and_wait(self, message):
        out = message
        message_length = len(message)
        first_mssg = self.create_segment((0,0,0,self.seq, str(message_length)))
        tries = 0
        ready = False
        while not ready:
            try:
                self.socket.sendto(first_mssg, self.destiny)
                data, addr = self.socket.recvfrom(1024)
                _, ack, _, seq, _ = self.parse_segment(data)
                if (seq == self.expected_seq) and ack:
                    ready = True
                    self.seq += 1
                    self.expected_seq +=1
                    tries = 0
                else:
                    continue
            except socket.timeout:
                continue
        
        while out:
            try:
                out_mssg = out[:BUFF_SIZE]
                out_seg = self.create_segment((0, 0, 0, self.seq, out_mssg))
                self.socket.sendto(out_seg, self.destiny)
                data, addr = self.socket.recvfrom(1024)
                syn, ack, fin, seq, _ = self.parse_segment(data)
                if ack and (seq == self.expected_seq):
                    out = out[BUFF_SIZE:]
                    self.expected_seq += 1
                    self.seq += 1
                    tries = 0
                else:
                    continue

            except socket.timeout:
                continue
    
    def recv_using_stop_and_wait(self, buff_size):
        head_length = len('0|||0|||0||||||') 
        calc_buffer = head_length + buff_size 
        while True:
            try:
                data, addr = self.socket.recvfrom(calc_buffer + len(str(self.expected_seq)))
                syn, ack, fin, seq, message_length = self.parse_segment(data)

                if seq == self.expected_seq:
                    first_ack = self.create_segment((0,1,0, seq, ''))
                    self.socket.sendto(first_ack, addr)
                    self.seq = seq
                    self.expected_seq = seq + 1
                    break
                    
            except socket.timeout:
                continue
                
        remaining_message = int(message_length)
        message = ''
        while remaining_message:
            try:
                if remaining_message > buff_size:
                
                    data, addr = self.socket.recvfrom(calc_buffer + len(str(self.expected_seq)))
                    _,_,_, seq, body = self.parse_segment(data)
                    if self.expected_seq == seq:
                        message += body.decode()
                        ack_seg = self.create_segment((0,1,0,seq,''))
                        self.socket.sendto(ack_seg, addr)
                        self.seq = seq
                        self.expected_seq = seq + 1
                        remaining_message -= buff_size
                    elif self.expected_seq > seq:
                        ack_seg = self.create_segment((0,1,0,seq,''))
                        self.socket.sendto(ack_seg, addr)

                    else:
                        continue
                
                else:
                    data, addr = self.socket.recvfrom(head_length + remaining_message + len(str(self.expected_seq)))
                    _,_,_, seq, body = self.parse_segment(data)
                    if self.expected_seq == seq:
                        message += body.decode()
                        ack_seg = self.create_segment((0,1,0,seq,''))
                        self.socket.sendto(ack_seg, addr)
                        self.seq = seq 
                        self.expected_seq = seq + 1
                        remaining_message -= remaining_message
                    
                    elif self.expected_seq > seq:
                        ack_seg = self.create_segment((0,1,0,seq,''))
                        self.socket.sendto(ack_seg, addr)
                    
                    else:
                        continue
            except socket.timeout:
                continue

        return message

    def send_using_go_back_n(self, message):
        out = message.encode()
        message_length = len(out)
        tries = 0
        ready = False
        ## out = [out[i:i+BUFF_SIZE] for i in range(0, message_length, BUFF_SIZE)]
        data_list = []
        while out:
            data_list.append( out[:BUFF_SIZE])
            out = out[BUFF_SIZE:]

        data_list = [str(message_length).encode()] + data_list
        
        sliding_window = slidingWindowCC.SlidingWindowCC(WINDOW_SIZE, data_list, self.seq)
        self.set_timer_list_length(1)
        self.seq -=1
        while sliding_window.get_data(0) is not None:
            for i in range(0, WINDOW_SIZE):
                if sliding_window.get_sequence_number(i):
                    if sliding_window.get_sequence_number(i) > self.seq:
                        self.seq = sliding_window.get_sequence_number(i)
                        
                        msg = self.create_segment((0,0,0,sliding_window.get_sequence_number(i),sliding_window.get_data(i).decode()))
                        if self.timer_list[0]:
                            self.stop_timer(0)
                        self.sendto(msg, self.destiny)
                
                
            
            try:
                response, addr = self.recvfrom(1024)
                syn, ack, fin, seq, _ = self.parse_segment(response)
                if ack and seq <= self.seq:
                    while sliding_window.get_sequence_number(0) != None:
                        if sliding_window.get_sequence_number(0) <= seq:
                            sliding_window.move_window(1)
                        else:
                            break
                    
            except TimeoutError:
                print("timeout")
                self.seq -= 1
                continue

    def recv_using_go_back_n(self, buff_size):
        head_length = len('0|||0|||0||||||') 
        calc_buffer = head_length + buff_size 
        while True:
            try:
                data, addr = self.socket.recvfrom(calc_buffer + len(str(self.expected_seq)))
                syn, ack, fin, seq, message_length = self.parse_segment(data)

                if seq == self.expected_seq:
                    
                    first_ack = self.create_segment((0,1,0, seq, ''))
                    self.socket.sendto(first_ack, addr)
                    self.seq = seq
                    self.expected_seq = seq + len(message_length)
                    break
                    
            except:
                continue
                
        remaining_message = int(message_length)
        message = b''
        while remaining_message:
            try:
                if remaining_message >= buff_size:
                
                    data, addr = self.socket.recvfrom(calc_buffer + len(str(self.expected_seq)))
                    _,_,_, seq, body = self.parse_segment(data)
                    if self.expected_seq == seq:
                        message += body
                        ack_seg = self.create_segment((0,1,0,seq,''))
                        self.socket.sendto(ack_seg, addr)
                        self.seq = seq
                        self.expected_seq = seq + buff_size
                        remaining_message -= buff_size
                    elif self.expected_seq > seq:
                        ack_seg = self.create_segment((0,1,0,seq,''))
                        self.socket.sendto(ack_seg, addr)

                    else:
                        continue
                
                else:
                    data, addr = self.socket.recvfrom(head_length + remaining_message + len(str(self.expected_seq)))
                    _,_,_, seq, body = self.parse_segment(data)
                    if self.expected_seq == seq:
                        message += body
                        ack_seg = self.create_segment((0,1,0,seq,''))
                        self.socket.sendto(ack_seg, addr)
                        self.seq = seq 
                        self.expected_seq = seq + len(body)
                        remaining_message -= len(body)
                    
                    elif self.expected_seq > seq:
                        ack_seg = self.create_segment((0,1,0,seq,''))
                        self.socket.sendto(ack_seg, addr)
                    
                    else:
                        continue
            except:
                continue

        return message.decode()


        
        
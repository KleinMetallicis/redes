import socket, sys

def parse_packet(IP_packet: bytes):
    address = IP_packet[:4]
    port = IP_packet[4:6]
    ttl = IP_packet[6:7]
    ID = IP_packet[7:11]
    offset = IP_packet[11:15]
    size = IP_packet[15:19]
    FLAG = IP_packet[19:20]
    msg = IP_packet[20:]

    
    
    
    parsed_address = []
    for byte in bytes(address):
        parsed_address += [str(byte)]
    
    parsed_address = ".".join(parsed_address)
    
    parsed_port = int.from_bytes(port)

    parsed_ttl = ttl[0]
    parsed_ID = int.from_bytes(ID)
    parsed_offset = int.from_bytes(offset)
    parsed_size = int.from_bytes(size)
    parsed_FLAG = FLAG[0]

    parsed_msg = msg.decode()

    return parsed_address, parsed_port, parsed_ttl, parsed_ID, parsed_offset, parsed_size, parsed_FLAG, parsed_msg

def create_packet(parsed_address, parsed_port, parsed_ttl, parsed_ID, parsed_offset, parsed_size, parsed_FLAG, msg):
    

    encoded = parsed_address.split(".")
    encoded = [int(elem).to_bytes(1) for elem in encoded]
    packet = bytearray()
    for x in encoded:
        packet.extend(x)
    packet.extend(int(parsed_port).to_bytes(2))

    packet.extend(int(parsed_ttl).to_bytes(1))

    packet.extend(int(parsed_ID).to_bytes(4))

    packet.extend(int(parsed_offset).to_bytes(4))

    packet.extend(int(parsed_size).to_bytes(4))

    packet.extend(int(parsed_FLAG).to_bytes(1))
    
    packet.extend(msg.encode())
    

    return bytes(packet)

def check_routes(round_robin: tuple[dict, dict, dict], destination_address: tuple[str, int]) -> (tuple[str, int], int):
    round_robin_count, round_robin_choices, round_robin_mtu = round_robin
    forward_options = list(round_robin_count.keys())

    ip_msg, port_msg = destination_address
    for route in forward_options:
        ip, min_port, max_port= route.split(", ")
        if (int(min_port) <= int(port_msg) <= int(max_port)) and (ip_msg in ip):
            count = round_robin_count[route]
            dest_address = round_robin_choices[route][count[0]%count[1]]
            dest_mtu = round_robin_mtu[route][count[0]%count[1]]
            round_robin_count[route][0] += 1
            return dest_address, int(dest_mtu)
                   
def create_rr_struct(routes_file_name: str):
    route_table = open(routes_file_name, "r")
    routes = route_table.read().splitlines()
    round_robin_count = dict()
    round_robin_choices = dict()
    round_robin_mtu = dict()
    for route in routes:
        ip, min_port, max_port, dest_ip, dest_port, mtu = route.split()
        try:
            round_robin_choices[f"{ip}, {min_port}, {max_port}"] += [(dest_ip, int(dest_port))]
            round_robin_count[f"{ip}, {min_port}, {max_port}"][1] += 1
            round_robin_mtu[f"{ip}, {min_port}, {max_port}"] += [mtu]
    
        except:
            round_robin_choices[f"{ip}, {min_port}, {max_port}"] = [(dest_ip, int(dest_port))]
            round_robin_count[f"{ip}, {min_port}, {max_port}"] = [0, 1]
            round_robin_mtu[f"{ip}, {min_port}, {max_port}"] = [mtu]
    
    return round_robin_count, round_robin_choices, round_robin_mtu
        
def fragment_IP_packet(IP_packet, MTU):
    if len(IP_packet) <= MTU:
        return [IP_packet]
    else:
        ip, port, ttl, ID, offset, size, FLAG, data = parse_packet(IP_packet)
        data_size = MTU - 20 #HEAD size
        packet_array = []
        
        while len(data) > data_size:
            frag_data = data[:data_size]
            packet_array += [create_packet(ip,port,ttl,ID, offset,len(frag_data), 1, frag_data)]
            offset += data_size
            data = data[data_size:]
        packet_array += [create_packet(ip,port,ttl,ID, offset, len(data), FLAG, data)]
        return packet_array
        
def reassemble_IP_packet(fragment_list):
    parsed_fragments = [parse_packet(x) for x in fragment_list]
    
    if (len(parsed_fragments) == 1) and not parsed_fragments[0][6] and not parsed_fragments[0][4]:
        return fragment_list[0]
    else:
        ordered_frags = []
        offset_list = [fragment[4] for fragment in parsed_fragments]
        while parsed_fragments:
            index = offset_list.index(min(offset_list))
            ordered_frags += [parsed_fragments[index]]
            parsed_fragments.pop(index)
            offset_list.pop(index)

        ordered_offset_list = [fragment[4] for fragment in ordered_frags]
        ordered_size_list = [fragment[5] for fragment in ordered_frags]
        if ordered_offset_list[0]:
            print("first value is not offset 0")
            return None
        
        if ordered_frags[-1][6]:
            print("not final packet")
            return None

        for i in range(len(ordered_frags)-1):
            if (ordered_offset_list[i] + ordered_size_list[i]) != ordered_offset_list[i+1]:
                print("missing packets")
                return None

        else:
            full_data = [fragment[-1] for fragment in ordered_frags]
            full_data = "".join(full_data)
            ip,port,ttl,ID, offset, size, FLAG, data = ordered_frags[0]
            reassembled_packet = create_packet(ip,port,ttl,ID,0,len(full_data),0,full_data)
            return reassembled_packet
        
        
        

        

if __name__ == "__main__":
    socket_address = (sys.argv[1], int(sys.argv[2]))
    route_table = sys.argv[3]

    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket.bind(socket_address)
    round_robin = create_rr_struct(route_table)

    recieved_msgs = dict()

    while True:
        msg, address = socket.recvfrom(1024)
        
        ip_msg, port_msg, ttl_msg, ID, offset, size, FLAG, text_msg = parse_packet(msg)
        if int(ttl_msg) > 0:
            if (ip_msg, int(port_msg)) == socket_address:
                try:
                    recieved_msgs[ID] += [msg]
                except:
                    recieved_msgs[ID] = [msg]
                reassembled_packet = reassemble_IP_packet(recieved_msgs[ID])
                #print(recieved_msgs[ID])
                if reassembled_packet:
                    print(parse_packet(reassembled_packet)[-1])
                
                
            else:
                dest_address, MTU = check_routes(round_robin, (ip_msg, int(port_msg)))
                if dest_address:
                    forward_packet = create_packet(ip_msg, port_msg, ttl_msg - 1, ID, offset, size, FLAG, text_msg)
                    packet_list = fragment_IP_packet(msg, MTU)
                    print(f"redirigiendo paquete {msg} con destino final {(ip_msg, port_msg)} desde {socket_address} hacia {dest_address}")
                    for packet in packet_list:
                        socket.sendto(packet, dest_address)
                else:
                    print(f"No hay rutas hacia {(ip_msg,port_msg)} para paquete {msg}")
        else:
            print(f"Se recibió paquete {msg} con TTL 0")

        


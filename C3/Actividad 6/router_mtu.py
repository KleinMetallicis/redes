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
    
    parsed_port = []
    for byte in bytes(port):
        parsed_port+=[str(byte).zfill(2)]
    
    parsed_port = "".join(parsed_port)

    parsed_ttl = ttl[0]
    parsed_ID = ID.decode()
    parsed_size = size.decode()
    parsed_FLAG = FLAG[0]

    parsed_msg = msg.decode()

    return parsed_address, parsed_port, parsed_ttl, parsed_ID, parsed_size, parsed_FLAG, parsed_msg

def create_packet(parsed_address, parsed_port, parsed_ttl, parsed_ID, parsed_size, parsed_FLAG, msg):
    

    encoded = parsed_address.split(".")
    encoded = [int(elem).to_bytes(1) for elem in encoded]
    packet = bytearray()
    for x in encoded:
        packet.extend(x)
    port = [parsed_port[:2]] + [parsed_port[2:]]
    
    for x in port:
        packet.extend(int(x).to_bytes(1))

    packet.extend(int(parsed_ttl).to_bytes(1))

    packet.extend(int(parsed_ID).to_bytes(4))

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
            return dest_address, dest_mtu
                   
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
        ip, port, ttl, ID, size, FLAG, data = parse_packet(IP_packet)
        data_size = MTU - 20 #HEAD size
        packet_array = []
        while len(data) > data_size:
            frag_data = data[:data_size]
            packet_array += [create_packet(ip,port,ttl,ID,len(frag_data), 1, frag_data)]
            data = data[data_size:]
        packet_array += [create_packet(ip,port,ttl,ID,len(data), 0, data)]
        return packet_array
        

        

if __name__ == "__main__":
    socket_address = (sys.argv[1], int(sys.argv[2]))
    route_table = sys.argv[3]

    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket.bind(socket_address)
    round_robin = create_rr_struct(route_table)

    while True:
        msg, address = socket.recvfrom(1024)
        ip_msg, port_msg, ttl_msg, text_msg = parse_packet(msg)
        if int(ttl_msg) > 0:
            if (ip_msg, int(port_msg)) == socket_address:
                print(text_msg)
            else:
                dest_address = check_routes(round_robin, (ip_msg, int(port_msg)))
                if dest_address:
                    print(f"redirigiendo paquete {msg} con destino final {(ip_msg, port_msg)} desde {socket_address} hacia {dest_address}")
                    forward_packet = create_packet(ip_msg, port_msg, ttl_msg - 1, text_msg)
                    socket.sendto(forward_packet, dest_address)
                else:
                    print(f"No hay rutas hacia {(ip_msg,port_msg)} para paquete {msg}")
        else:
            print(f"Se recibió paquete {msg} con TTL 0")

        


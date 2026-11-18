import socket, sys

def parse_packet(IP_packet: bytes):
    address = IP_packet[:4]
    port = IP_packet[4:6]
    msg = IP_packet[6:]

    
    
    
    parsed_address = []
    for byte in bytes(address):
        parsed_address += [str(byte)]
    
    parsed_address = ".".join(parsed_address)
    
    parsed_port = int.from_bytes(port)

    parsed_msg = msg.decode()

    return parsed_address, parsed_port, parsed_msg

def create_packet(parsed_address, parsed_port, msg):
    

    encoded = parsed_address.split(".")
    encoded = [int(elem).to_bytes(1) for elem in encoded]
    packet = bytearray()
    for x in encoded:
        packet.extend(x)
    port = int(parsed_port).to_bytes(2)
    
    packet.extend(port)
    
    
    packet.extend(msg.encode())
    

    return bytes(packet)

def check_routes( round_robin: tuple[dict, dict], destination_address: tuple[str, int]) -> tuple[str, int]:
    round_robin_count, round_robin_choices = round_robin
    forward_options = list(round_robin_count.keys())

    ip_msg, port_msg = destination_address
    for route in forward_options:
        ip, min_port, max_port= route.split(", ")
        if (int(min_port) <= int(port_msg) <= int(max_port)) and (ip_msg in ip):
            count = round_robin_count[route]
            dest_address = round_robin_choices[route][count[0]%count[1]]
            round_robin_count[route][0] += 1
            return dest_address
                   
def create_rr_struct(routes_file_name: str):
    route_table = open(routes_file_name, "r")
    routes = route_table.read().splitlines()
    round_robin_count = dict()
    round_robin_choices = dict()
    for route in routes:
        ip, min_port, max_port, dest_ip, dest_port = route.split()
        try:
            round_robin_choices[f"{ip}, {min_port}, {max_port}"] += [(dest_ip, int(dest_port))]
            round_robin_count[f"{ip}, {min_port}, {max_port}"][1] += 1
        except:
            round_robin_choices[f"{ip}, {min_port}, {max_port}"] = [(dest_ip, int(dest_port))]
            round_robin_count[f"{ip}, {min_port}, {max_port}"] = [0, 1]
    
    return round_robin_count, round_robin_choices
        

if __name__ == "__main__":
    socket_address = (sys.argv[1], int(sys.argv[2]))
    route_table = sys.argv[3]

    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket.bind(socket_address)
    round_robin = create_rr_struct(route_table)

    while True:
        msg, address = socket.recvfrom(1024)
        ip_msg, port_msg, text_msg = parse_packet(msg)
        if (ip_msg, int(port_msg)) == socket_address:
            print(text_msg)
        else:
            dest_address = check_routes(round_robin, (ip_msg, int(port_msg)))
            if dest_address:
                print(f"redirigiendo paquete {msg} con destino final {(ip_msg, port_msg)} desde {socket_address} hacia {dest_address}")
                socket.sendto(msg, dest_address)
            else:
                print(f"No hay rutas hacia {(ip_msg,port_msg)} para paquete {msg}")


        


from router_with_ttl import create_packet as create_packet_ttl
from router import create_packet
import socket
import sys




    

if __name__ == "__main__":
    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if sys.argv[1] == "basic":
        ip_ini, port_ini, ip_dest, port_dest, msg = sys.argv[2:]
        ip_packet = create_packet(ip_dest, port_dest, msg)
        socket.sendto(ip_packet, (ip_ini, int(port_ini)))
    elif sys.argv[1] == "TTL":
        ip_ini, port_ini, ip_dest, port_dest, ttl, msg = sys.argv[2:]
        ip_packet = create_packet(ip_dest, port_dest, ttl, msg)
        socket.sendto(ip_packet, (ip_ini, int(port_ini)))
    

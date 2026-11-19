from router_mtu import create_packet
import sys

if __name__ == "__main__":
    result = open("encoded_msg", "wb+")
    ip, port, ttl, ID = sys.argv[1:]
    msg = sys.stdin.buffer.read().decode()
    msg = create_packet(ip, port, ttl, ID, 0, len(msg), 0, msg)
    
    result.write(msg)
from router_with_ttl import create_packet
import sys

if __name__ == "__main__":
    result = open("encoded_msg", "wb+")
    ip, port, ttl, msg = sys.argv[1:]
    msg = create_packet(ip, port, ttl, msg)
    result.write(msg)
from router import create_packet
import sys

if __name__ == "__main__":
    result = open("encoded_msg", "wb+")
    ip, port, msg = sys.argv[1:]
    msg = create_packet(ip, port, msg)
    result.write(msg)
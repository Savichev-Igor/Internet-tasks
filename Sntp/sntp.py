import socket
import struct

HOST = "time.nist.gov"
PORT = 123

# FORMAT = "B"

FORMAT = "BBBBII4sQQQQ"


def main():
    UDP = socket.getprotobyname('udp')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, UDP)
    s.settimeout(3.0)
    s.connect((HOST, PORT))
    # print(struct.calcsize(FORMAT))
    packet = struct.Struct(FORMAT)
    packet_bin = packet.pack((4 << 3) | 3, 0, 0, 0, 0, 0, b'Hi', 0, 0, 0, 0)
    # packet_bin = packet.pack((4 << 3) | 3, 0, 0, 0)
    print('SEND')
    # s.sendall(packet_bin)
    # packet = b'35' + b'0'*46
    # print(packet)
    s.sendall(packet_bin)
    print('RECV')
    packet_bin = s.recv(48)
    # print(struct)
    # print(packet_bin)
    print(packet.unpack(packet_bin))

if __name__ == "__main__":
    main()


# import socket, struct, sys, time
# TIME1970 = 2208988800  # Thanks to F.Lundh
# client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# client.connect(("time.nist.gov", 123))
# print(hex(35))
# print(bin(35))
# print(hex(27))
# print(bin(27))
# print(4<<3|3)
# data = bin(27) + '0' * 47
# print(data[2:])
# print(len(data))
# client.sendall(data[2:].encode())
# data, address = client.recvfrom(1024)
# if data:
#     print('Response received from:', address)
#     print(data)
#     t = struct.unpack('!12I', data)[10]
#     print(t)
#     t -= TIME1970
#     print('\tTime = %s' % time.ctime(t))

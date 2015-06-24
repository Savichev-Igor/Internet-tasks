# !/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import argparse
import struct
import re

from errno import ECONNREFUSED
from multiprocessing import Pool


def createParser():
    parser = argparse.ArgumentParser(
            prog='python portscan.py',
            description="""Эта программа сканирует TCP/UDP порты.
                        """,
            epilog='''(c) Puni, 2015. Автор программы, как всегда,
                      не несет никакой ответственности.
                   '''
            )
    parser.add_argument("HOST", type=str,
                        help="IP адрес удаленного компьютера")
    parser.add_argument("PORTS", type=str,
                        help="Диапазон портов")
    return parser


class Portscan:

    PACKETS = {
        "ntp":      b'\x1b' + 47 * b'\0',

        "dns":      b'\x1b\xc8\x01\x00\x00\x01\x00'
                    b'\x00\x00\x00\x00\x00\x03\x77'
                    b'\x77\x77\x10\x67\x6f\x6f\x67'
                    b'\x6c\x65\x2d\x61\x6e\x61\x6c'
                    b'\x79\x74\x69\x63\x73\x03\x63'
                    b'\x6f\x6d\x00\x00\x01\x00\x01',

        "smtp":     b'HELO Portscan',

        "pop3":     b'\x16\x03\x01\x00\xb0\x01\x00'
                    b'\x00\xac\x03\x03\xc8\xff'
                    b'\x13\x29\xdc\x74\x6d\xc0'
                    b'\xec\x34\xef\xd5\x37\xac'
                    b'\x01\x2c\x08\xb8\xec\x9c'
                    b'\x94\x65\x87\x09\x96\x09'
                    b'\x08\x73\x49\x3b\xd4\x1e'
                    b'\x00\x00\x2e\xc0\x2b\xc0'
                    b'\x2f\xc0\x0a\xc0\x09\xc0'
                    b'\x13\xc0\x14\xc0\x12\xc0'
                    b'\x07\xc0\x11\x00\x33\x00'
                    b'\x32\x00\x45\x00\x39\x00'
                    b'\x38\x00\x88\x00\x16\x00'
                    b'\x2f\x00\x41\x00\x35\x00'
                    b'\x84\x00\x0a\x00\x05\x00'
                    b'\x04\x01\x00\x00\x55\x00'
                    b'\x00\x00\x17\x00\x15\x00'
                    b'\x00\x12\x70\x6f\x70\x2e'
                    b'\x67\x6f\x6f\x67\x6c\x65'
                    b'\x6d\x61\x69\x6c\x2e\x63'
                    b'\x6f\x6d\xff\x01\x00\x01'
                    b'\x00\x00\x0a\x00\x08\x00'
                    b'\x06\x00\x17\x00\x18\x00'
                    b'\x19\x00\x0b\x00\x02\x01'
                    b'\x00\x00\x23\x00\x00\x00'
                    b'\x05\x00\x05\x01\x00\x00'
                    b'\x00\x00\x00\x0d\x00\x12'
                    b'\x00\x10\x04\x01\x05\x01'
                    b'\x02\x01\x04\x03\x05\x03'
                    b'\x02\x03\x04\x02\x02\x02',

        "http":     b'\x47\x45\x54\x20\x2f\x63\x6c'
                    b'\x2f\x37\x38\x30\x32\x39\x34'
                    b'\x33\x61\x32\x64\x39\x66\x34'
                    b'\x37\x36\x61\x38\x31\x37\x31'
                    b'\x36\x33\x61\x32\x34\x39\x32'
                    b'\x63\x64\x30\x30\x66\x20\x48'
                    b'\x54\x54\x50\x2f\x31\x2e\x31'
                    b'\x0d\x0a\x68\x6f\x73\x74\x3a'
                    b'\x32\x31\x33\x2e\x32\x34\x38'
                    b'\x2e\x31\x31\x37\x2e\x32\x34'
                    b'\x38\x0d\x0a\x75\x73\x65\x72'
                    b'\x2d\x61\x67\x65\x6e\x74\x3a'
                    b'\x41\x6b\x61\x6d\x61\x69\x20'
                    b'\x4e\x65\x74\x53\x65\x73\x73'
                    b'\x69\x6f\x6e\x20\x49\x6e\x74'
                    b'\x65\x72\x66\x61\x63\x65\x20'
                    b'\x28\x36\x31\x66\x36\x63\x31'
                    b'\x37\x3b\x77\x69\x6e\x3b\x31'
                    b'\x2e\x39\x2e\x31\x2e\x35\x3b'
                    b'\x57\x69\x6e\x38\x29\x0d\x0a'
                    b'\x0d\x0a'
        }

    def __init__(self, ip_addr):
        self.ip_addr = ip_addr

    def check_TCP(self, port):
        self.s_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_TCP.settimeout(0.1)
        try:
            self.con = self.s_TCP.connect((self.ip_addr, port))
            result = port, 'unknown'
            for packet in Portscan.PACKETS:
                try:
                    self.s_TCP.sendall(Portscan.PACKETS[packet])
                    data = self.s_TCP.recv(1024)
                    result = port, self.which_proto(data)
                    break
                except socket.error as msg_1:
                    # print(msg_1)
                    continue
            try:
                self.con.close()
                self.s_TCP.close()
            except:
                pass
            return result
        except socket.error as msg_2:
            # print(msg_2)
            if msg_2.errno == ECONNREFUSED:
                return False

    def check_UDP(self, port):
        self.s_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s_UDP.settimeout(0.1)
        try:
            self.s_UDP.sendto(b"LOL", (self.ip_addr, port))
            try:
                f_data = self.s_UDP.recv(1024)
                print(f_data)
                result = port, 'unknown'
                for packet in Portscan.PACKETS:
                    try:
                        self.s_UDP.sendto(Portscan.PACKETS[packet], (self.ip_addr, port))
                        data = self.s_UDP.recv(1024)
                        result = port, self.which_proto(data)
                        break
                    except socket.error as msg_1:
                        # print(mgs_1)
                        continue
            except socket.error as msg_2:
                # print(msg_2)
                return False
            try:
                self.s_UDP.close()
            except:
                pass
            return result
        except socket.error as msg_3:
            # print(msg_3)
            return False

    def is_dns(self, data):
        try:
            header = struct.unpack("!HH", data[:4])
            if not header[1] & 0x0001:
                if len(data) > 200:
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False

    def is_http(self, data):
        try:
            header = data[:4]
            if header == b"HTTP":
                return True
            else:
                return False
        except:
            return False

    def is_ntp(self, data):
        try:
            header = data
            struct.unpack("!12I", header)
            return True
        except:
            return False

    def is_smtp(self, data):
        try:
            nums = re.match(r"([0-5])([0-5])([0-5])", data.decode())
            if nums:
                return True
            else:
                return False
        except:
            return False

    def which_proto(self, data):
        if self.is_http(data):
            return "www-http"

        elif self.is_smtp(data):
            return "smtp"

        elif self.is_dns(data):
            return "dns"

        elif self.is_ntp(data):
            return "ntp"
        else:
            return 'unknown'


def main():
    p = createParser()
    args = p.parse_args()
    PORTS = args.PORTS.split('-')
    start = int(PORTS[0])
    end = int(PORTS[1])+1
    print()
    p = Pool(50)
    s = Portscan(args.HOST)
    result_TCP = list(filter(bool, p.map(s.check_TCP, range(start, end))))  # All ports and + 1
    result_UDP = list(filter(bool, p.map(s.check_UDP, range(start, end))))  # All ports and + 1
    for res in result_TCP:
        print(str(res) + ' TCP port is Open')
    for res in result_UDP:
        print(str(res) + ' UDP port is Open')

if __name__ == "__main__":
    main()

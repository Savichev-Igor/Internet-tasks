# !/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import socket
import re
import argparse

import os
import struct


def createParser():
    parser = argparse.ArgumentParser(
            prog='sudo python3 traceroute.py',
            description="""Эта программа аналог Unix Tracerout'a""",
            epilog='''(c) Puni ,2015. Автор программы, как всегда,
                       не несет никакой ответственности.'''
            )
    parser.add_argument('destination', type=str,
                        help="Ip адрес для трассировки")
    parser.add_argument("--Hops", "-H", type=int, default=30,
                        help="количество хопов")
    return parser


F1 = "BBHHH"
F2 = "H"


def calculate_checksum(source_string):
    """
    A port of the functionality of in_cksum() from ping.c
    Ideally this would act on the string as a series of 16-bit ints (host
    packed), but this works.
    Network data is big-endian, hosts are typically little-endian
    """
    countTo = (int(len(source_string) / 2)) * 2
    sum = 0
    count = 0

    # Handle bytes in pairs (decoding as short ints)
    loByte = 0
    hiByte = 0
    while count < countTo:
        if (sys.byteorder == "little"):
            loByte = source_string[count]
            hiByte = source_string[count + 1]
        else:
            loByte = source_string[count + 1]
            hiByte = source_string[count]
        sum = sum + (ord(hiByte) * 256 + ord(loByte))
        count += 2

    # Handle last byte if applicable (odd-number of bytes)
    # Endianness should be irrelevant in this case
    if countTo < len(source_string): # Check for odd length
        loByte = source_string[len(source_string) - 1]
        sum += ord(loByte)

    sum &= 0xffffffff # Truncate sum to 32 bits (a variance from ping.c, which
                      # uses signed ints, but overflow is unlikely in ping)

    sum = (sum >> 16) + (sum & 0xffff)  # Add high 16 bits to low 16 bits
    sum += (sum >> 16)                  # Add carry from above (if any)
    answer = ~sum & 0xffff              # Invert and truncate to 16 bits
    answer = socket.htons(answer)

    return answer

def checksum(icmp):  # Контрольная сумма
    s = 0
    for i in range(0, len(icmp), 2):
        t = struct.unpack(F2, icmp[i:i+2])[0]+s
        s = (t & 0xFFFF) + (t >> 16)
    return ~s & 0xFFFF


def request():  # ICMP REQUEST
    p = struct.Struct(F1)
    temp_packet = p.pack(8, 0, 0, 0, 0)
    packet = struct.pack(F1, 8, 0, calculate_checksum(temp_packet), 0, 0)
    return packet


class Traceroute:

    def __init__(self, dest_name, max_hops):
        self.dest_addr = socket.gethostbyname(dest_name)
        # self.dest_name = dest_name
        self.port = 33434
        self.max_hops = max_hops
        # ICMP = socket.getprotobyname('icmp')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self.s.settimeout(3.0)
        # self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, ICMP)
        # self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        # self.recv_socket.settimeout(3.0)
        # self.recv_socket.bind(("", self.port))
        self.regexp_iana = re.compile('whois:(.+)')
        self.regexp_reg_AS = re.compile(':.+(as\d+)')
        self.regexp_reg_country = re.compile('country:(.+)')
        self.regexp_reg_provider = re.compile('descr:(.+)')

    def start(self):
        # UDP = socket.getprotobyname('udp')
        ttl = 1
        while True:
            # send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, UDP)
            self.s.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            self.s.sendto(request(), (self.dest_addr, self.port))
            # send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            # send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
            # send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
            # send_socket.sendto(b'', (self.dest_addr, self.port))
            curr_addr = None
            curr_name = None
            try:
                _, curr_addr = self.s.recvfrom(512)
                curr_addr = curr_addr[0]
                try:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]
                except socket.error:
                    curr_name = curr_addr
            except socket.error:
                pass
            if curr_addr is not None:
                server = self.whois_iana(curr_addr)
                if server is not None:
                    info = self.whois_region(server, curr_addr)
                curr_host = "%s (%s)" % (curr_name, curr_addr)
            else:
                curr_host = "* * *"
            print("%d\t%s" % (ttl, curr_host))
            print('\n')
            if curr_host != "* * *" and server is not None:
                for key in info:
                    print("\t%s: %s" % (key, info[key]))
                print('\n')
            else:
                for i in range(3):
                    print("\t%s" % ("***"))
                print('\n')
            ttl += 1
            if curr_addr == self.dest_addr:
                print('\nNice, we got addres with %s hops' % (self.max_hops))
                break
            if ttl > self.max_hops:
                print('Hops ended... :<')
                break
        self.s.close()

    def whois_iana(self, ip_addr):
        ip_addr += '\r\n'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("whois.iana.org", 43))
        # s.setblocking(0)    # Если не может прочитать - кидает эксепшн
        buf = ""
        s.send(ip_addr.encode())
        try:
            while True:
                temp = s.recv(1024)
                if len(temp) > 0:
                    buf += temp.decode('utf-8')
                else:
                    break
        except socket.error:
            pass
        finally:
            s.close()
        # print(buf)
        res = re.search(self.regexp_iana, buf)
        try:
            need_server = res.groups()[0].strip()
        except:
            return None
        return need_server

    def whois_region(self, server, ip_addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip_addr += '\r\n'
        s.connect((server, 43))
        # try:
        #     print(s.recv(1024))    # Приветствие пропустили
        # except:
        #     pass
        s.send(ip_addr.encode())
        buf = ""
        try:
            while True:
                temp = s.recv(1024)
                if len(temp) > 0:
                    buf += temp.decode('utf-8')
                else:
                    break
        except socket.error:
                pass
        finally:
            s.close()
        dict_info = {}
        # print(buf)
        buf = buf.lower()
        AS = re.search(self.regexp_reg_AS, buf)
        country = re.search(self.regexp_reg_country, buf)
        provider = re.search(self.regexp_reg_provider, buf)
        dict_info.update({"server": server})
        try:
            dict_info.update({"AS": AS.groups()[0].strip().upper()})
        except:
            dict_info.update({"AS": "***"})
        try:
            dict_info.update({"country": country.groups()[0].strip().upper()})
        except:
            dict_info.update({'country': "***"})
        try:
            dict_info.update({"provider":
                              provider.groups()[0].strip().upper()})
        except:
            dict_info.update({'provider': "***"})
        return dict_info


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            os.system("netsh advfirewall firewall add rule name=ICMPV4 dir=in action=allow protocol=icmpv4 >nul")
            print("Создано правило открытия портов для ICMPV4!")
        p = createParser()
        args = p.parse_args()
        print("\nTraceroute for %s with %s hops...\n" % (args.destination,
                                                         args.Hops))
        A = Traceroute(args.destination, args.Hops)
        A.start()
    finally:
        if sys.platform == "win32":
            os.system("netsh advfirewall firewall delete rule name=ICMPV4 dir=in protocol=icmpv4 >nul")
            print("Удалено правило открытия портов для ICMPV4!")

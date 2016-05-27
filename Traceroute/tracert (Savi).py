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
            prog="python traceroute.py",
            description="""Эта программа аналог Tracerout'a,
                           (Tracert).
                        """,
            epilog='''(c) Puni, 2015. Автор программы, как всегда,
                       не несет никакой ответственности.
                   '''
            )
    parser.add_argument("destination", type=str,
                        help="Ip адрес для трассировки")
    parser.add_argument("--Hops", "-H", type=int, default=30,
                        help="количество хопов")
    return parser


def take_packet():
    packet = struct.Struct("BBHHH")
    bin_packet = packet.pack(8, 0, 0xfff7, 0, 0)  # 65 527
    return bin_packet


class Traceroute:

    regexp_iana = re.compile("whois:(.+)")
    regexp_reg_AS = re.compile("origin:.+as(\d+)")
    regexp_reg_country = re.compile("country:(.+)")
    regexp_reg_provider = re.compile("descr:(.+)")

    def __init__(self, dest_name, max_hops):
        self.dest_addr = socket.gethostbyname(dest_name)
        # self.dest_name = dest_name
        self.port = 33434
        self.max_hops = max_hops
        self.bin_packet = take_packet()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                               socket.IPPROTO_ICMP)
        self.s.settimeout(3.0)

    def start(self):
        ttl = 1
        while True:
            res = ""
            self.s.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            self.s.sendto(self.bin_packet, (self.dest_addr, self.port))
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
            res += "%d\t%s\n" % (ttl, curr_host)
            if curr_host != "* * *" and server is not None:
                for key in info:
                    res += "\t%s: %s\n" % (key, info[key])
            else:
                for i in range(3):
                    res += "\t%s\n" % ("***")
            ttl += 1
            yield res
            if curr_addr == self.dest_addr:
                break
            if ttl > self.max_hops:
                break
        self.s.close()

    def whois_iana(self, ip_addr):
        ip_addr += "\r\n"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(("whois.iana.org", 43))
        except:
            return None
        # s.setblocking(0)  # Если не может прочитать - кидает эксепшн
        buf = self.reader(s, ip_addr)
        res = Traceroute.regexp_iana.search(buf)
        try:
            need_server = res.groups()[0].strip()
        except:
            return None
        return need_server

    def whois_region(self, server, ip_addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip_addr += "\r\n"
        s.connect((server, 43))
        # try:
        #     print(s.recv(1024))  # Приветствие пропустили
        # except:
        #     pass
        buf = self.reader(s, ip_addr)
        dict_info = {}
        buf = buf.lower()
        AS = Traceroute.regexp_reg_AS.search(buf)
        country = Traceroute.regexp_reg_country.search(buf)
        provider = Traceroute.regexp_reg_provider.search(buf)
        dict_info["server"] = server
        try:
            dict_info["AS"] = AS.groups()[0].strip().upper()
        except:
            dict_info["AS"] = "***"
        try:
            dict_info["country"] = country.groups()[0].strip().upper()
        except:
            dict_info["country"] = "***"
        try:
            dict_info["provider"] = provider.groups()[0].strip().upper()
        except:
            dict_info["provider"] = "***"
        return dict_info

    def reader(self, s, ip_addr):
        buf = ""
        s.send(ip_addr.encode())
        try:
            while True:
                temp = s.recv(1024)
                if len(temp) > 0:
                    buf += temp.decode("utf-8")
                else:
                    break
        except socket.error:
            pass
        finally:
            s.close()
        return buf

if __name__ == "__main__":
    try:
        p = createParser()
        args = p.parse_args()
        if sys.platform == "win32":
            os.system("netsh advfirewall firewall add rule name=ICMPV4 \
                       dir=in action=allow protocol=icmpv4 > nul")
        print("\nTraceroute for %s with %s hops...\n" % (args.destination,
                                                         args.Hops))
        A = Traceroute(args.destination, args.Hops)
        gen = A.start()
        for info in gen:
            print(info)
    finally:
        if sys.platform == "win32":
            os.system("netsh advfirewall firewall delete rule name=ICMPV4 \
                       dir=in protocol=icmpv4 > nul")

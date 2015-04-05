# !/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import threading
import argparse
# import time


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


# ports_TCP = []


class Scanner_TCP(threading.Thread):

    def __init__(self, ip_addr, port):
        threading.Thread.__init__(self)
        self.daemon = True
        self.ip_addr = ip_addr
        self.port = port
        self.TCP = socket.getprotobyname('TCP')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, self.TCP)
        self.s.settimeout(0.1)

    def run(self):
        try:
            self.s.connect((self.ip_addr, self.port))
            try:
                print('TCP: {0} {1} {2}'.format(self.ip_addr,
                                                self.port,
                                                socket.getservbyport(self.port)))
            except socket.error as msg_2:
                print('TCP: {0} {1}'.format(self.ip_addr, self.port))
            # global ports_TCP
            # ports_TCP.append(self.port)
            self.s.close()
        except socket.error as msg_1:
            pass

# ports_UDP = []


class Scanner_UDP(threading.Thread):

    def __init__(self, ip_addr, port):
        threading.Thread.__init__(self)
        self.daemon = True
        self.ip_addr = ip_addr
        self.port = port
        self.UDP = socket.getprotobyname('UDP')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, self.UDP)
        self.s.settimeout(0.1)

    def run(self):
        try:
            self.s.sendto(b"LOL", (self.ip_addr, self.port))
            try:
                self.s.recv(1024)
                try:
                    print('UDP: {0} {1} {2}'.format(self.ip_addr,
                                                    self.port,
                                                    socket.getservbyport(self.port)))
                except socket.error as msg_3:
                    print('UDP: {0} {1}'.format(self.ip_addr, self.port))
            except socket.error as ms_2:
                pass
            # global ports_UDP
            # ports_UDP.append(self.port)
            self.s.close()
        except socket.error as msg_1:
            pass


def main():
    p = createParser()
    args = p.parse_args()
    PORTS = args.PORTS.split('-')
    print()
    for port in range(int(PORTS[0]), int(PORTS[1])+1):  # All ports and + 1
        Scanner_TCP(args.HOST, port).start()
        Scanner_UDP(args.HOST, port).start()

if __name__ == "__main__":
    main()

# !/usr/bin/python
# -*- coding: utf-8 -*-
# import sys
import socket
import time

import struct
import argparse

HOST = "127.0.0.1"
PORT = 8000

FORMAT = "BBBBII4sQQQQ"

TIME1970 = 2208988800  # Thanks to F.Lundh


def createParser():
    parser = argparse.ArgumentParser(
            prog='python sntp_client.py',
            description="""Это клиент для sntp server'a.
                           Поставляется вместе с sntp сервером,
                           смотреть в папке.
                        """,
            epilog='''(c) Puni, 2015. Автор программы, как всегда,
                      не несет никакой ответственности.
                   '''
            )
    return parser


class Client():

    def __init__(self):
        self.packet = struct.Struct(FORMAT)
        UDP = socket.getprotobyname('UDP')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, UDP)

    def send_request(self):
        packet_bin = self.packet.pack(0b00100011, 0, 0, 0, 0, 0, b'Hi',
                                      0, 0, 0, self.get_time())
        self.s.sendto(packet_bin, (HOST, PORT))

    def get_reply(self):
        answer_packet_bin = self.s.recv(1024)
        # t4 = self.get_time()  # Время приёма пакета клиентом
        # t1 = self.packet.unpack(answer_packet_bin)[8]  # Начальн. отпр. кл-ом
        # t2 = self.packet.unpack(answer_packet_bin)[9]  # Приём сервером
        t3 = self.packet.unpack(answer_packet_bin)[10]  # Отправка сервером
        self.s.close()
        # print(self.get_offset(t1, t2, t3, t4))
        return time.ctime(self.get_normal_time(t3))
        # return time.ctime(self.get_normal_time(t3) -
        #                   self.get_offset(t1, t2, t3, t4))

    def get_time(self):
        t = int((time.time() + TIME1970) * 2**32)
        return t

    def get_normal_time(self, t):
        t = (t // 2**32) - TIME1970
        return t

    def get_offset(self, t1, t2, t3, t4):
        """ В этой функции мы высчитываем поправку
            исходя из всем известной формулы t = ((t2 - t1) + (t3 - t4)) // 2
        """
        t1 = self.get_normal_time(t1)
        t2 = self.get_normal_time(t2)
        t3 = self.get_normal_time(t3)
        t4 = self.get_normal_time(t4)
        return ((t2 - t1) + (t3 - t4)) // 2


def main():
    p = createParser()
    p.parse_args()
    A = Client()
    try:
        A.send_request()
        time = A.get_reply()
        print(time)
    except Exception as e:
        # print(e)
        print("\nSomething is wrong")

if __name__ == "__main__":
    main()

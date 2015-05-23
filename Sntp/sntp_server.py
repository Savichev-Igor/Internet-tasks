# !/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import socket
import time
from concurrent.futures import ThreadPoolExecutor

import struct
import argparse

FORMAT = "BBBBII4sQQQQ"

TIME1970 = 2208988800  # Thanks to F.Lundh

HOST = "0.0.0.0"
PORT = 8000


def createParser():
    parser = argparse.ArgumentParser(
            prog='python sntp_server.py',
            description="""Эта программа аналог sntp сервера, но врущего.
                        """,
            epilog='''(c) Puni, 2015. Автор программы, как всегда,
                      не несет никакой ответственности.
                   '''
            )
    parser.add_argument("Offset", type=int,
                        help="На сколько солгать")
    return parser


class Server:

    def __init__(self, s, addr, query_packet, offset):
        self.daemon = True
        self.s = s
        self.addr = addr
        self.query_packet = query_packet
        self.offset = offset

    def answer(self):
        self.s.sendto(self.create_answer(), self.addr)
        return "OK"

    def create_answer(self):
        """ В этой функции мы фиксируем время приёма пакета,
            копируем в соответствующее поле время отправки запроса клиентом,
            также фиксируем время отправки ответа.
        """
        # time.sleep(1.5)  # Чтобы имитировать, что сервер думает
        recv_time = self.get_time()
        # time.sleep(1.0)  # Аналогично
        try:
            data = struct.unpack(FORMAT, self.query_packet)
            answer_packet = struct.Struct(FORMAT)
            answer_packet_bin = answer_packet.pack(0b00100100, 1,
                                                   0, 0, 0, 0, b'Savi',
                                                   0, data[10],
                                                   recv_time,
                                                   self.get_time())
            return answer_packet_bin
        except Exception as e:
            pass    # Не реагируем на плохие пакеты

    def get_time(self):
        t = int((time.time() + TIME1970 + self.offset) * 2**32)
        return t


def main():
    try:
        p = createParser()
        args = p.parse_args()
        UDP = socket.getprotobyname('UDP')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, UDP)
        s.bind((HOST, PORT))
        with ThreadPoolExecutor(max_workers=3) as pool:
            while True:
                query_packet, addr = s.recvfrom(1024)
                query = Server(s, addr, query_packet, args.Offset)
                pool.submit(query.answer)
    except KeyboardInterrupt as error:
        s.close()
        print('\nYou killed program :<')
        sys.exit(0)

if __name__ == "__main__":
    main()

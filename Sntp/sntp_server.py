# !/usr/bin/python
# -*- coding: utf-8 -*-
import sys
# import signal
import socket
import time
import threading

import struct
import argparse

FORMAT = "BBBBII4sQQQQ"

TIME1970 = 2208988800  # Thanks to F.Lundh

HOST = "0.0.0.0"
PORT = 123


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


class Server(threading.Thread):

    def __init__(self, ip_addr, port, client, offset):
        threading.Thread.__init__(self)
        self.daemon = True
        self.ip_addr = ip_addr
        self.port = port
        self.client = client
        self.offset = offset

    def run(self):
        # self.client.settimeout(3)
        self.client.sendall(self.create_answer())
        self.client.shutdown(socket.SHUT_WR)   # Дочитает - закроет
        self.client.close()

    def create_answer(self):
        """ В этой функции мы фиксируем время приёма пакета,
            копируем в соответствующее поле время отправки запроса клиентом,
            также фиксируем время отправки ответа.
        """
        # time.sleep(1.5)  # Чтобы имитировать, что сервер думает
        packet_bin = self.client.recv(1024)
        recv_time = self.get_time()
        # time.sleep(1.0)  # Аналогично
        try:
            data = struct.unpack(FORMAT, packet_bin)
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


# def handler(signum, frame):
    # s.close()
    # print('\nWe closed socket')


def main():
    try:
        # signal.signal(signal.SIGTSTP, handler)
        # signal.signal(signal.SIGINT, handler)
        # global s
        p = createParser()
        args = p.parse_args()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(10)
        while True:
            client, (ip_addr, port) = s.accept()
            print(ip_addr, port)
            Server(ip_addr, port, client, args.Offset).start()
    except KeyboardInterrupt as error:
        s.close()
        print('\nYou killed program :<')
        sys.exit(0)

if __name__ == "__main__":
    main()

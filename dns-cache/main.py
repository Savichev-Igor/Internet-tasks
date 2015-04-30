# !/usr/bin/python3
# -*- coding: utf-8 -*-
import socket
import threading
# import argparse
# import time
import sys
# import struct

HOST = '0.0.0.0'
PORT = 8000


class Server(threading.Thread):

    def __init__(self, ip_addr, port, client):
        threading.Thread.__init__(self)
        self.daemon = True
        self.ip_addr = ip_addr
        self.port = port
        self.client = client

    def run(self):
        # self.client.settimeout(3)
        self.client.sendall(self.create_answer())
        self.client.shutdown(socket.SHUT_WR)   # Дочитает - закроет
        self.client.close()


def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(100)
        while True:
            client, (ip_addr, port) = s.accept()
            print(ip_addr, port)
            Server(ip_addr, port, client).start()
    except Exception as error:
        s.close()
        print('\nSad :<\n')
        print(error)
        sys.exit(0)

if __name__ == "__main__":
    main()

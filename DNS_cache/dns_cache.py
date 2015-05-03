# !/usr/bin/python3
# -*- coding: utf-8 -*-
import socket
import threading
import argparse
import time
import sys
import struct

HOST = '127.0.0.1'  # Адрес сервера
PORT = 53  # Порт сервера


cache = dict()  # Наш кэш


def createParser():
    parser = argparse.ArgumentParser(
            prog='python dns_cache.py',
            description="""Эта программа выполняет функции кэширующего DNS сервера
                           на 127.0.0.1 8000
                        """,
            epilog='''(c) Puni, 2015. Автор программы, как всегда,
                      не несет никакой ответственности.
                   '''
            )
    parser.add_argument("forwarder", type=str,
                        help="Вышестоящий сервер")
    parser.add_argument("f_port", type=int,
                        help="Порт вышестоящего сервера")
    return parser


class DNS_Packet():     # Класс для работы с DNS пакетом

    def __init__(self, data):
        """ Типичный конструктор класса... """
        self.data = data
        self.data_HEADER = None
        self.QNAME = None
        self.len_name = None
        self.QTYPE = None
        self.QCLASS = None
        self.ATYPE = None
        self.ACLASS = None

    def get_header(self):
        """ В этой функции извлекаем HEADER запроса """
        self.data_HEADER = struct.unpack('!HHHHHH', self.data[0:12])
        # return struct.unpack('!HHHHHH', self.data[0:12])

    def set_id(self, ID):
        reply_ID = struct.pack("!H", ID)
        self.data = reply_ID + self.data[2:]

    def get_q_name(self):
        """ Здесь извлекаем ИМЯ из запроса, для которого хотим получить IP """
        name_length = 0
        for i in self.data[12:]:
            name_length += 1
            if i == 0 or i == struct.pack('B', 0):
                break
        name = self.data[12:12+name_length]
        self.len_name = name_length
        self.QNAME = struct.unpack(str(self.len_name)+'s', name)
        # return struct.unpack(str(self.len_name)+'s', name)

    def get_type(self, part):
        """ Здесь получаем тип для запроса или ответа """
        types = {
            1: 'A',
            2: 'NS',
            3: 'MD',
            4: 'MF',
            5: 'CNAME',
            6: 'SOA',
            7: 'MB',
            8: 'MG',
            9: 'MR',
            10: 'NULL',
            11: 'WKS',
            12: 'PTR',
            13: 'HINFO',
            14: 'MINFO',
            15: 'MX',
            16: 'TXT'
        }
        if part == 'QUESTION':
            type_of_query = struct.unpack('!H', self.data[12+self.len_name:12+self.len_name+2])[0]
            self.QTYPE = types[type_of_query]
            # return types[type_of_query]
        if part == 'ANSWER':
            type_of_answer = struct.unpack('!H', self.data[12+self.len_name+4+2:12+self.len_name+4+4])[0]
            self.ATYPE = types[type_of_answer]
            # return types[type_of_answer]

    def get_class(self, part):
        """ Аналогично получаем класс для запроса или ответа """
        classes = {
            1: 'IN',
            2: 'CS',
            3: 'CH',
            4: 'HS',
        }
        if part == 'QUESTION':
            class_of_query = struct.unpack('!H', self.data[12+self.len_name+2:12+self.len_name+4])[0]
            self.QCLASS = classes[class_of_query]
            # return classes[class_of_query]
        if part == 'ANSWER':
            class_of_answer = struct.unpack('!H', self.data[12+self.len_name+4+4:12+self.len_name+4+6])[0]
            self.ACLASS = classes[class_of_answer]
            # return classes[class_of_answer]

    def set_q_name(self, name):
        """ Здесь мы немного меняем имя, а точнее убираем '\x03www.'
            из первоначального запроса, чтобы не делать лишних заросов к
            форвардеру, и чтобы кэш понимал, что www.e1.ru и e1.ru одно
            и тоже """
        self.QNAME = name,
        self.data = self.data[:12] + struct.pack(str(len(name))+"s", name) + self.data[12+self.len_name:]
        self.len_name = len(name)

    def get_ttl(self, begin, end):
        """ Получаем TTL ответа """
        # self.TTL = struct.unpack('!I', self.data[12+self.len_name+4+6:12+self.len_name+4+10])
        return struct.unpack('!I', self.data[begin:end])[0]

    def get_rdata_len(self, begin, end):
        """ Получаем длину RDATA """
        return struct.unpack('!H', self.data[begin:end])[0]

    def set_ttl(self, cache_time, cache_ttl):
        """ Устанавливаем новый TTL для каждого ответа """
        begin = 12 + self.len_name + 4 + 10    # Сдвиги для получения RDATA_len
        end = 12 + self.len_name + 4 + 12
        for ans in range(self.data_HEADER[3]):    # Количество ответов
            RD_len = self.get_rdata_len(begin, end)
            # print(RD_len)
            # print(self.get_ttl(begin-4, end-2))
            new_ttl = struct.pack('!I', int(cache_ttl - time.time() + cache_time))
            self.data = self.data[0:begin-4] + new_ttl + self.data[end-2:]
            begin += RD_len + 12
            end += RD_len + 12

    def parse_query(self):
        """ Просто функция обработки запроса"""
        self.get_header()
        self.get_q_name()
        # self.get_type('QUESTION')
        # self.get_class('QUESTION')

    def parse_answer(self):
        """ Просто функция обработки ответа """
        self.get_header()
        self.get_q_name()
        # self.get_type('ANSWER')
        # self.get_class('ANSWER')


class DNS_Server(threading.Thread):

    def __init__(self, data, client, forwarder, f_port, s_UDP):
        threading.Thread.__init__(self)
        self.daemon = True
        self.data = data    # Оригинальный запрос
        self.client = client    # Кому отвечать
        self.forwarder = forwarder
        self.f_port = f_port
        self.s_UDP = s_UDP

    def ask_forwarder(self, key):
        print("\nASK FORWARDER\n")
        forwarder_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forwarder_s.settimeout(0.1)
        try:
            forwarder_s.sendto(self.data, (self.forwarder, self.f_port))
            response = forwarder_s.recv(4096)
            response_packet = DNS_Packet(response)
            response_packet.parse_answer()
            print(response_packet.QNAME)
            self.s_UDP.sendto(response_packet.data, self.client)
            begin = 12 + response_packet.len_name + 4 + 6
            end = 12 + response_packet.len_name + 4 + 10
            cache[key] = [response_packet, time.time(), response_packet.get_ttl(begin, end)]
            # print(cache)
        except socket.error:
            print("Wait a momemnt...")

    def run(self):
        request = DNS_Packet(self.data)
        request.parse_query()     # Первично обработали пакет
        # if b'\x03www' in request.QNAME[0]:
            # print('here_1')
            # print(request.data)
            # request.set_q_name(request.QNAME[0][4:])
            # print(request.data,)
        key = request.data[2:]
        if key in cache:
            cache_data = cache[key][0].data
            cache_time = cache[key][1]
            cache_ttl = cache[key][2]
            if time.time() - cache_time <= cache_ttl:
                print("\nTaking from cache\n")
                reply_packet = DNS_Packet(cache_data)
                reply_packet.parse_answer()
                print(reply_packet.QNAME)
                reply_packet.set_id(request.data_HEADER[0])
                reply_packet.set_ttl(cache_time, cache_ttl)
                self.s_UDP.sendto(reply_packet.data, self.client)
            else:
                self.ask_forwarder(key)
        else:
            self.ask_forwarder(key)


def main():
    try:
        p = createParser()
        args = p.parse_args()
        if args.forwarder == '127.0.0.1' and args.f_port == PORT:
            args.forwarder = '8.8.8.8'
            args.f_port = 53
        s_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_UDP.bind((HOST, PORT))
        while True:
            data, addr = s_UDP.recvfrom(4096)
            # print(data, addr)
            # print(cache)
            DNS_Server(data, addr, '8.8.8.8', 53, s_UDP).start()
    except Exception as error:
        s_UDP.close()
        print(error)
        sys.exit(0)

if __name__ == "__main__":
    main()

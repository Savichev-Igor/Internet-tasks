# !/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import socket
import ssl
import re

from email.header import decode_header


class POP3_SSL():

    def __init__(self, server, port, login, password, start, end):
        self.server = server
        self.port = port
        self.login = login
        self.password = password
        self.current = 1
        self.amount_of_mails = None
        self.start = start
        self.end = end
        self.mails = None
        self.to_regexp = re.compile("To:\s(.+)", re.IGNORECASE)
        self.from_regexp = re.compile("From:\s(.+)", re.IGNORECASE)
        self.subject_regexp = re.compile("Subject:\s(.+)", re.IGNORECASE)
        self.date_regexp = re.compile("Date:\s(.+)", re.IGNORECASE)
        self.size_regexp = re.compile("\+OK\s(\d+)\s")

    def connection(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_socket = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
        self.ssl_socket.settimeout(1)
        try:
            self.ssl_socket.connect((self.server, self.port))
            ans = self.reader(self.ssl_socket)
            sys.stderr.write(ans)
            if ans[1:3] == 'OK':
                print("\nConnection is success\n")
            else:
                raise ValueError
        except Exception as er:
            print("\nWe can't connection to POP3 server\n")
            print(er)
            sys.exit()

    def auth(self):
        login = 'USER' + ' ' + self.login + '\r\n'
        password = 'PASS' + ' ' + self.password + '\r\n'
        try:
            self.ssl_socket.send(login.encode())
            ans = self.reader(self.ssl_socket)
            sys.stderr.write(ans)
            if ans[1:3] != "OK":
                raise ValueError
            self.ssl_socket.send(password.encode())
            ans = self.reader(self.ssl_socket)
            sys.stderr.write(ans)
            if ans[1:3] != "OK":
                raise ValueError
        except Exception as er:
            print('\nSomething wrong with your pass or login\n')
            print(er)
            sys.exit()

    def list(self):
        try:
            self.ssl_socket.send(b"LIST\r\n")
            ans = self.reader(self.ssl_socket)
            sys.stderr.write(ans)
        except Exception as er:
            print('\nSomething is going wrong...\n')
            print(er)
            sys.exit()

    def stat(self):
        regexp = re.compile('\+OK\s(\d+)\s')
        try:
            self.ssl_socket.send(b"STAT\r\n")
            ans = self.reader(self.ssl_socket)
            sys.stderr.write(ans)
            self.amount_of_mails = int(regexp.findall(ans)[0])
        except Exception as er:
            print('\nSomething is going wrong...\n')
            print(er)
            sys.exit()

    def get_mails(self):
        mails = list()
        retr_template = "RETR {0}\r\n"
        if self.amount_of_mails < self.end:
            self.end = self.amount_of_mails
        # f = open('check.txt', 'wb')
        for current_mail in range(self.start, self.end + 1, 1):
            try:
                self.ssl_socket.send(retr_template.format(current_mail).encode())
                ans = self.byte_reader(self.ssl_socket)
                # sys.stderr.write(ans)
                # print(current_mail)
                # f.write(str(current_mail).encode())
                # f.write(ans)
                # f.write(b'\n')
                # print(current_mail)
                subj = self.parse_subj(ans)
                dec_subj = self.decode_header(subj)
                from_who = self.parse_from(ans)
                dec_from_who = self.decode_header(from_who)
                general_info = self.parse_general(ans)
                to = general_info[1]
                dec_to = self.decode_header(to)
                mails.append({'№: ': current_mail,
                              'Subject: ': dec_subj,
                              'From: ': dec_from_who,
                              'Size: ': general_info[0] + ' bytes',
                              'To: ': dec_to,
                              'Date: ': general_info[2]})
            except Exception as er:
                print(er)
                print("\nSomething is wrong with {0} mail\n".format(current_mail))
                continue
        # f.close()
        self.mails = mails

    def parse_general(self, data):
        to_flag = True
        date_flag = True
        size_flag = True
        ans = list()
        for line in str(data).split('\\r\\n'):
            if size_flag:
                size = self.size_regexp.findall(line)
                if len(size) > 0:
                    ans.append(size[0])
                    size_flag = False
            if to_flag:
                to = self.to_regexp.findall(line)
                if len(to) > 0:
                    ans.append(to[0])
                    to_flag = False
            if date_flag:
                date = self.date_regexp.findall(line)
                if len(date) > 0:
                    ans.append(date[0])
                    date_flag = False
            if not to_flag and not date_flag and not size_flag:
                break
        return ans

    def parse_subj(self, data):
        flag = False
        subj = ""
        for line in str(data).split('\\r\\n'):
            if flag:
                if 'From' in line or 'To' in line:
                    break
                else:
                    if '=?' in line:
                        subj += line
            else:
                sub = self.subject_regexp.findall(line)
                if len(sub) > 0:
                    flag = True
                    subj += sub[0]
        # print(subj)
        return subj

    def parse_from(self, data):
        flag = False
        from_who = ""
        for line in str(data).split('\\r\\n'):
            if flag:
                if 'To' in line or 'Subject' in line:
                    break
                else:
                    from_who += line
            else:
                sub = self.from_regexp.findall(line)
                if len(sub) > 0:
                    flag = True
                    from_who += sub[0]
        # print(from_who)
        return from_who

    def decode_header(self, data):
        dec = decode_header(data)
        f_dec = ""
        for i in range(len(dec)):
            if dec[i][1] != None:
                f_dec += dec[i][0].decode(dec[i][1])
            else:
                if type(dec[i][0]) == type('str'):
                    f_dec += dec[i][0]
                else:
                    f_dec += dec[i][0].decode()
        return f_dec

    def reader(self, s):
        ans = b''
        while True:
            try:
                temp = s.recv(1024)
                if temp:
                    ans += temp
            except Exception as er:
                # print(er)
                break
        return ans.decode("UTF-8")

    def byte_reader(self, s):
        ans = b''
        while True:
            try:
                temp = s.recv(1024)
                if temp:
                    ans += temp
            except Exception as er:
                # print(er)
                break
        return ans

    def cute_print(self):
        for mail in self.mails:
            print('\n\n')
            for key in mail:
                print(key, end='')
                print(mail[key])


def main():
    p = None
    p.connection()
    p.auth()
    # p.list()
    p.stat()
    p.get_mails()
    p.cute_print()

if __name__ == "__main__":
    main()
# !/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import socket
import ssl
import re
import argparse

from email.header import decode_header


def createParser():
    parser = argparse.ArgumentParser(
            prog="python3 pop3.py",
            description="""Эта программа выводит неплохую информацию о вашей почте,
                           по протоколу pop3
                        """,
            epilog='''(c) Savi, 2015. Автор программы, как всегда,
                       не несет никакой ответственности.
                   '''
            )
    parser.add_argument("pop_server", type=str,
                        help="Адрес POP сервера")
    parser.add_argument("--port", "-p", type=int, default=995,
                        help="Порт POP сервера")
    parser.add_argument("login", type=str,
                        help="Ваш логин для почты")
    parser.add_argument("password", type=str,
                        help="Ваш пароль для почты")
    parser.add_argument("--rang", "-r", type=str, default="1-1",
                        help="Диапазон извелчения писем, в формате \d-\d. (По умолчанию = 1-1)")
    return parser


class POP3_SSL():

    to_regexp = re.compile("To:\s(.+)", re.IGNORECASE)
    from_regexp = re.compile("From:\s(.+)", re.IGNORECASE)
    subject_regexp = re.compile("Subject:\s(.+)", re.IGNORECASE)
    date_regexp = re.compile("Date:\s(.+)", re.IGNORECASE)
    size_regexp = re.compile("\+OK\s(\d+)\s")
    boundary_regexp = re.compile("boundary=(.*?)[\n;]")
    file_name = re.compile("filename='(.*)'")
    base_data = re.compile("\n([A-z0-9+/\n=\s]+)\n")

    def __init__(self, server, port, login, password, start, end):
        self.server = server
        self.port = port
        self.login = login
        self.password = password
        self.current = 1
        self.amount_of_mails = None
        self.start = start
        self.end = end

    def connection(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_socket = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
        self.ssl_socket.settimeout(1)
        try:
            self.ssl_socket.connect((self.server, self.port))
            ans = self.reader(self.ssl_socket)
            sys.stderr.write("\n")
            sys.stderr.write(ans)
            if ans[1:3] == "OK":
                print("\nConnection is success\n")
            else:
                raise ValueError
        except Exception:
            print("\nWe can't connection to POP3 server\n")
            sys.exit()

    def end_connection(self):
        self.ssl_socket.close()

    def auth(self):
        login = "USER" + " " + self.login + "\r\n"
        password = "PASS" + " " + self.password + "\r\n"
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
        except Exception:
            print("\nSomething wrong with your pass or login\n")
            sys.exit()

    def list(self):
        try:
            self.ssl_socket.send(b"LIST\r\n")
            ans = self.reader(self.ssl_socket)
            sys.stderr.write(ans)
        except Exception:
            print("\nSomething is going wrong...\n")
            sys.exit()

    def stat(self):
        regexp = re.compile("\+OK\s(\d+)\s")
        try:
            self.ssl_socket.send(b"STAT\r\n")
            ans = self.reader(self.ssl_socket)
            sys.stderr.write(ans)
            self.amount_of_mails = int(regexp.findall(ans)[0])
        except Exception:
            print("\nSomething is going wrong...\n")
            sys.exit()

    def get_mails(self):
        retr_template = "RETR {0}\r\n"
        if self.amount_of_mails < self.end:
            self.end = self.amount_of_mails
        print("\n")
        for current_mail in range(self.start, self.end + 1, 1):
            try:
                print("Getting mail № {0}...".format(current_mail))
                self.ssl_socket.send(retr_template.format(current_mail).encode())
                ans = self.byte_reader(self.ssl_socket)
                subj = self.parse_subj(ans)
                dec_subj = self.decode_header(subj)
                from_who = self.parse_from(ans)
                dec_from_who = self.decode_header(from_who)
                general_info = self.parse_general(ans)
                to = general_info["To"]
                dec_to = self.decode_header(to)
                atts = self.get_size_att(ans)
                mail = {"№: ": current_mail,
                        "Subject: ": dec_subj,
                        "From: ": dec_from_who,
                        "Size: ": general_info["Size"] + " bytes",
                        "To: ": dec_to,
                        "Date: ": general_info["Date"],
                        "Attachments: ": atts}
                self.cute_print(mail)
            except Exception:
                print("\nSomething is wrong with {0} mail\n".format(current_mail))
                continue
        self.end_connection()

    def parse_general(self, data):
        to_flag = True
        date_flag = True
        size_flag = True
        ans = {"Size": "unknown", "To": "", "Date": ""}
        for line in str(data).split("\\r\\n"):
            if size_flag:
                size = POP3_SSL.size_regexp.findall(line)
                if len(size) > 0:
                    ans["Size"] = size[0]
                    size_flag = False
            if to_flag:
                to = POP3_SSL.to_regexp.findall(line)
                if len(to) > 0:
                    ans["To"] = to[0]
                    to_flag = False
            if date_flag:
                date = POP3_SSL.date_regexp.findall(line)
                if len(date) > 0:
                    ans["Date"] = date[0]
                    date_flag = False
            if not to_flag and not date_flag and not size_flag:
                break
        return ans

    def parse_subj(self, data):
        flag = False
        subj = ""
        for line in str(data).split("\\r\\n"):
            if flag:
                if "From" in line or "To" in line or "Date" in line or "Content-Type" in line:
                    break
                else:
                    if "=?" in line:
                        subj += line
            else:
                sub = POP3_SSL.subject_regexp.findall(line)
                if len(sub) > 0:
                    flag = True
                    subj += sub[0]
        return subj.replace("\\t", "")

    def parse_from(self, data):
        flag = False
        from_who = ""
        for line in str(data).split("\\r\\n"):
            if flag:
                if "To" in line or "Subject" in line or "Date" in line or "Content-Type" in line:
                    break
                else:
                    from_who += line
            else:
                sub = POP3_SSL.from_regexp.findall(line)
                if len(sub) > 0:
                    flag = True
                    from_who += sub[0]
        return from_who.replace("\\t", "")

    def get_size_att(self, data):
        atts_sizes = dict()
        b = POP3_SSL.boundary_regexp.findall(data.decode())
        if len(b) >= 1:
            b = b[-1]
            b = b.replace('"', "")
            b = b.replace("'", '')
            for line in data.decode().split(b):
                name = POP3_SSL.file_name.search(line)
                if name:
                    f_name = str(name.groups()[0])
                    s = POP3_SSL.base_data.findall(line)
                    if s:
                        s = s[0]
                        atts_sizes[f_name] = str((len(s) * 6) // 8) + " bytes"
                    else:
                        atts_sizes[f_name] = "unknows bytes"
        return atts_sizes

    def decode_header(self, data):
        dec = decode_header(data)
        f_dec = ""
        for i in range(len(dec)):
            if dec[i][1] is not None:
                f_dec += dec[i][0].decode(dec[i][1])
            else:
                if type(dec[i][0]) == type("str"):
                    f_dec += dec[i][0]
                else:
                    f_dec += dec[i][0].decode()
        return f_dec

    def reader(self, s):
        ans = b""
        while True:
            try:
                temp = s.recv(1024)
                if temp:
                    ans += temp
            except Exception:
                break
        return ans.decode("UTF-8")

    def byte_reader(self, s):
        ans = b""
        while True:
            try:
                temp = s.recv(1024)
                if temp:
                    ans += temp
            except Exception:
                break
        return ans

    def cute_print(self, mail):
        print("\n")
        for key in mail:
            try:
                print(key, end="")
                print(mail[key])
            except Exception:
                print("Something is wrong with encoding")
        print("\n")


def main():
    A = createParser()
    args = A.parse_args()
    if args.rang:
        rang = args.rang.split("-")
        start = int(rang[0])
        end = int(rang[1])
    else:
        start = 1
        end = 1
    p = POP3_SSL(args.pop_server, args.port, args.login, args.password, start, end)
    p.connection()
    p.auth()
    p.stat()
    p.get_mails()

if __name__ == "__main__":
    main()

# !/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from os import walk, getcwd
import ssl
import socket
import re
import base64
import argparse


def createParser():
    parser = argparse.ArgumentParser(
            prog='python smtp_mime.py',
            description="""Эта программа отправляет все картинки
                           в виде вложений из указанного каталога или
                           рабочего каталога.
                        """,
            epilog='''(c) Savi, 2015. Автор программы, как всегда,
                      не несет никакой ответственности.
                   '''
            )
    parser.add_argument("e_mail", type=str,
                        help="Адреса получателя")
    parser.add_argument("IP", type=str,
                        help="IP Сервера SMTP")
    parser.add_argument("PORT", type=int,
                        help="Порт Сервера SMTP")
    parser.add_argument("PATH", type=str, default=getcwd(), nargs='?',
                        help="Путь к картинкам, по умолчанию - рабочий каталог")
    parser.add_argument("--Login", "-L", type=str, default=None,
                        help="Логин для авторизации в почте")
    parser.add_argument("--Pass", "-P", type=str, default=None,
                        help="Пароль для авторизации в почте")
    return parser


class SMTP:

    def __init__(self, server, port, rcpt_to, path, login=None, password=None):
        self.server = server
        self.port = port
        self.login = login
        self.password = password
        self.rcpt_to = rcpt_to
        self.path = path
        self.type_security = None
        # self.PIPELING = False    Ну он используется, в общем
        if port == 587:
            self.type_security = 'TLS'
        elif port == 965 or port == 465:
            self.type_security = 'SSL'

    def connect_ssl(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_socket = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
        self.ssl_socket.settimeout(1.5)
        try:
            self.ssl_socket.connect((self.server, self.port))
            ans = self.reader(self.ssl_socket)
            sys.stderr.write(ans)
            if ans[0:3] == '220':
                print("\nConnection is success\n")
            else:
                raise ValueError
            self.ehlo(self.ssl_socket)
        except Exception as er:
            print("\nWe can't connection to SMTP_SSL server\n")
            print(er)
            sys.exit()

    def connect_tls(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        try:
            s.connect((self.server, self.port))
            ans = self.reader(s)
            sys.stderr.write(ans)
            if ans[0:3] == '220':
                print("\nConnection is success\n")
            else:
                raise ValueError
            self.ehlo(s)
            s.send(b'STARTTLS\r\n')
            ans = self.reader(s)
            sys.stderr.write(ans)
            if ans[0:3] == '220':
                print('\nOkay, we start TLS connection\n')
                self.tls_socket = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLSv1)
                self.ehlo(self.tls_socket)
            else:
                raise ValueError
        except Exception as er:
            print("\nWe can't connection to SMTP_TLS server\n")
            print(er)
            sys.exit()

    def get_only_images_base64(self):
        re_images = re.compile('(jpeg|jpg|png|bmp|gif)')
        dict_images = dict()
        files = []
        for (dir_path, dir_names, file_names) in walk(self.path):
            files.extend(file_names)
            break
        for f in files:
            if len(re_images.findall(f)) > 0:
                with open(self.path+"/"+f, "rb") as normal_file:
                    encoded_string = base64.standard_b64encode(normal_file.read())
                    dict_images[f] = encoded_string
        return dict_images

    def simple_connection(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(1.5)
        try:
            self.s.connect((self.server, self.port))
            ans = self.reader(self.s)
            sys.stderr.write(ans)
            if ans[0:3] == '220':
                print("\nConnection is success\n")
            else:
                raise ValueError
            self.ehlo(self.s)
        except Exception as er:
            print("\nWe can't connection to SMTP_SSL server\n")
            print(er)
            sys.exit()

    def send_mail(self):
        try:
            if self.type_security == "TLS":
                self.connect_tls()
                sock = self.tls_socket
                self.auth(self.tls_socket)
                self.body_letter(self.tls_socket)
            elif self.type_security == "SSL":
                self.connect_ssl()
                sock = self.ssl_socket
                self.auth(self.ssl_socket)
                self.body_letter(self.ssl_socket)
            elif not self.login and not self.password:
                self.simple_connection()
                sock = self.s
                self.body_letter(sock)
        except Exception as er:
            print("\nSomething is going wrong...\n")
            print(er)
            sys.exit()

    def auth(self, socket):
        socket.send(b'AUTH LOGIN\r\n')
        ans = self.reader(socket)
        sys.stderr.write(ans)
        b64_login = base64.b64encode(self.login.encode())
        socket.send(b64_login + b'\r\n')
        ans = self.reader(socket)
        sys.stderr.write(ans)
        b64_password = base64.b64encode(self.password.encode())
        socket.send(b64_password + b'\r\n')
        ans = self.reader(socket)
        sys.stderr.write(ans)

    def body_letter(self, socket):
        rcpt_to_template = "rcpt to: <{0}>\r\n"
        PIPELINING_command = "mail from: <{0}>".format(self.login) + '\r\n'
        # for adr in self.rcpt_to.split(' '):
        PIPELINING_command += rcpt_to_template.format(self.rcpt_to)
        PIPELINING_command += "data\r\n"
        socket.send(PIPELINING_command.encode())
        ans = self.reader(socket)
        sys.stderr.write(ans)
        data = self.get_data().encode()
        socket.send(data)
        socket.send(b".\r\n")
        ans = self.reader(socket)
        sys.stderr.write(ans)
        if ans[0:3] == "250":
            print("\nLetter was send\n")
        socket.send(b"quit\r\n")
        socket.close()

    def get_data(self):
        start_template = "From: Good Guy <{0}>\r\n"
        to_template = ""
        for_who = "To: Bad Guy <{0}>\r\n"
        # for adr in self.rcpt_to.split(' '):
        to_template += for_who.format(self.rcpt_to)
        message_template = ("Subject: Get It !\r\n"
                            "Content-Type: multipart/mixed; boundary=xyz\r\n"
                            "\r\n"
                            "--xyz\r\n"
                            "Content-Type: text/html; charset=utf-8\r\n"
                            "\r\n"
                            "<h1> What do u think about pictures :3 ?</h1>\r\n"
                            "\r\n"
                            "--xyz\r\n")
        attachments = "attachments:\r\n"
        dict_images = self.get_only_images_base64()
        for f in dict_images:
            attachments += f + "\r\n"
        attachments += "\r\n"
        attachments += "--xyz\r\n"
        files_template = ""
        image_b64_template = ('Content-Type: image/{0}\r\n'
                              'Content-Disposition: attachment; filename="{1}"\r\n'
                              'Content-Transfer-Encoding: base64\r\n')
        counter = 0
        for f in dict_images:
            counter += 1
            if counter == len(dict_images):
                files_template += image_b64_template.format(f[f.index(".")+1:], f) +\
                                  "\r\n" + str(dict_images[f].decode("UTF-8")) + '\r\n' + '--xyz--\r\n'
            else:
                files_template += image_b64_template.format(f[f.index(".")+1:], f) +\
                                  "\r\n" + str(dict_images[f].decode("UTF-8")) + '\r\n' + '--xyz\r\n'
        final_template = start_template.format(self.login) + to_template +\
                         message_template + attachments + files_template
        # with open("check.txt", "w") as t:
        #     t.write(final_template)
        return final_template

    def ehlo(self, s):
        try:
            s.send(b"EHLO Savi\r\n")
            ans = self.reader(s)
            sys.stderr.write(ans)
            if ans[0:3] == '250':
                print('\nIntroduce is success\n')
            else:
                raise ValueError
        except Exception as er:
            print("\nWe are unable to introduce yourself to the server\n")
            print(er)
            sys.exit()

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


def main():
    try:
        p = createParser()
        args = p.parse_args()
        s = SMTP(args.IP, args.PORT, args.e_mail, args.PATH.replace('\\', '/'), args.Login, args.Pass)
        s.send_mail()
    except Exception as er:
        print("\nSad\n")
        print(er)
        sys.exit()

if __name__ == "__main__":
    main()

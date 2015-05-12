# !/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from os import walk
import ssl
import socket
import re
import base64


class SMTP:

    def __init__(self, server, port, login, password, rctp_to):
        self.server = server
        self.port = port
        self.login = login
        self.password = password
        self.rcpt_to = rcpt_to
        self.type_security = None
        # self.PIPELING = False    Ну он используется, в общем
        if port == 587:
            self.type_security = 'TLS'
        elif port == 965:
            self.type_security = 'SSL'

    def connect_ssl(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_socket = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
        self.ssl_socket.settimeout(1)
        try:
            self.ssl_socket.connect((self.server, self.port))
            ans = self.reader(ssl_socket)
            sys.stderr.write(ans)
            if ans[0:3] == '220':
                print("\nConnection is success\n")
            else:
                raise ValueError
        except Exception as er:
            print("\nWe can't connection to SMTP_SSL server\n")
            print(er)
            sys.exit()

    def connect_tls(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
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

    def get_only_images_base64(self, path):
        re_images = re.compile('(jpeg|jpg|png|bmp|gif)')
        dict_images = dict()
        files = []
        for (dir_path, dir_names, file_names) in walk(path):
            files.extend(file_names)
            break
        for f in files:
            if len(re_images.findall(f)) > 0:
                with open(path+"/"+f, "rb") as normal_file:
                    encoded_string = base64.standard_b64encode(normal_file.read())
                    dict_images[f] = encoded_string
        return dict_images

    def simple_connection(self):
        pass

    def send_mail_TLS(self):
        self.connect_tls()
        self.tls_socket.send(b'AUTH LOGIN\r\n')
        ans = self.reader(self.tls_socket)
        sys.stderr.write(ans)
        b64_login = base64.b64encode(self.login.encode())
        self.tls_socket.send(b64_login + b'\r\n')
        ans = self.reader(self.tls_socket)
        sys.stderr.write(ans)
        b64_password = base64.b64encode(self.password.encode())
        self.tls_socket.send(b64_password + b'\r\n')
        ans = self.reader(self.tls_socket)
        sys.stderr.write(ans)

    def send_mail(self):
        start_template = """FROM: Good Guy <{0}>
To: Bad Guy <{1}}>
Subject: Получай !
Content-Type: multipart/mixed; boundary=xyz
--xyz
Content-Type: text/html; charset=utf-8

<h1> What do u think about pictures :3 ?</h1>

--xyz"""
        print(start_template)

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
        return ans


def simple_socket(server, port, login, password, rcpt_to):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))
    print(s.recv(1024))
    s.send(b'EHLO Savi\r\n')
    print(s.recv(1024))
    s.send(b'STARTTLS\r\n')
    print(s.recv(1024))
    tls_socket = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLSv1)
    tls_socket.send(b'EHLO Savi\r\n')
    print(tls_socket.recv(1024))
    # tls_socket.send(b'PIPELINING\r\n')
    # print(tls_socket.recv(1024))
    tls_socket.send(b'AUTH LOGIN\r\n')
    print(tls_socket.recv(1024))
    b64_login = base64.b64encode(login.encode())
    # print(b64_login)
    tls_socket.send(b64_login + b'\r\n')
    print(tls_socket.recv(1024))
    b64_password = base64.b64encode(password.encode())
    # print(b64_password)
    tls_socket.send(b64_password + b'\r\n')
    print(tls_socket.recv(1024))
    # print('hey')
    test_string = b'mail from: <Rick_Grimes72@mail.ru>\r\n' + b'rcpt to: <ultimate95@mail.ru>\r\n' + b'data\r\n'
    tls_socket.send(test_string)
    # tls_socket.send(b'mail from: <Rick_Grimes72@mail.ru>\r\n')
    print(tls_socket.recv(1024))
    # tls_socket.send(b'rcpt to: <ultimate95@mail.ru>\r\n')
    # print(tls_socket.recv(1024))
    # tls_socket.send(b'data\r\n')
    # print(tls_socket.recv(1024))
    tls_socket.send(data + '\r\n')
    tls_socket.send(b'.\r\n')
    print(tls_socket.recv(1024))
    tls_socket.send(b'quit\r\n')
    print(tls_socket.recv(1024))
#     message = """
# mail from: <BILL_GATES@mail.ru>\r\n
# rcpt to: <ultimate95@mail.ru>\r\n
# data\r\n
# Darova !\r\n
# Check homework, please !\r\n
# .\r\n
# Quit\r\n
#               """
    # tls_socket.send(message.encode())
    # print(tls_socket.recv(1024))

data = b"""From: Good Guy <Rick_Grimes72@mail.ru>
To: Bad Guy <savi@hackerdom.ru>
To: Bad Guy 1 <Ultimate95@mail.ru>
Subject: Получай !
Content-Type: multipart/related; boundary=xyz

--xyz
Content-Type: text/html; charset=utf-8

<h1> What do u think about pictures :3 ?</h1>

--xyz
attachments:
lol.png

--xyz
Content-Type: image/png
Content-Disposition: attachment; filename="lol.png"
Content-Transfer-Encoding: base64

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
ith2tPA4sVQ41LK5YzAHN1DCxfN6hTazojDkSahGh64+Fxf2wjsmO8xLben4JPtWPqRU08yWQv0b
apw363guPWcLuKYOk+VSKwv9jHjYI91mrqs42J7GedyOf9+sKbZQjrTxnfL+UnpibDYprLEvyi74
nU0IwXnc5IGOx2I9KUw4qLatj2+eW39M9zN97qVZ8WH6iPpFwrTx+dzDx6Ic8T7XCLiWGEX3Xrg4
KdyQA3xD5du9p/Pb9lTLY7HcZmob/Bo6vW2unxGuhTeZQ/CQ+rTYVprv63gslhdSBuYLuC4Trrmf
EbeZa7wh+JD6M+w57R3bLmaE21r5Zr2fwFw/I2wzq6wheJs8b2KbOOvxKFanmRPjEYpGj2K7zZSK
woW3RfSpv2OM1WjPQ+uo0mJqLuCaAind/Yy4zVzn3ASfUuepjIdStKwJWV2a1Tj4Nf9dqLufCRk9
inATvEv+DuFc2tcy6xnZ43uktys3/F2ou58RtpkSW+EtFefa1f51e+xh3ZF3KHva+fYzChe3mSW2
Mf2izYOZboeiqYS3XXMoJ/oB15QU2j73UGNzKBH5+5Z3a19LwDV2y6HcNsA319tgzNaKifAHWOFy
KGPq79eWB/1/3y2HcmQC8NRDhds2PEqHyaMIHcrCxHOhBec+lpLuVfXBFrVhtuhQTo0AntLtHR7Z
8CgDJo9SVal5MzPlKJVJ2d9zaWd2bKvFTG9SdhLW8zXPeqZMHkXoUKZkQ/nGpe/W2wkbiZaGmX0L
ayg8kdRlkLm4Vmh+pUnI4lGEDmXhd3psaia3l+axbDkUFHZNNC06SsXVlfzPbeyjDFk8itChDMi/
XFq+b/dSPJb7Fr5Ypb5v98wBrlwqjpKPEGq+Dn/G4lGaKg7l3FwioNZoXr8J5MgdEz6061DUCT9a
9n/WvPggvD9inWEPJaRnlHquPjjdUeU7YYRnxYRHlh2KKuFHS09YaQ4KhZeFVxk2ZYfkerTtzIP5
9Can286Y8I6JWJV9rrD1fPnGlu6hgmhc32JwKDNyj3nflQfz+U18+64k4VOLU54/d5pyaeH2ieCE
VWjje0/KowjP8vToAY7Gvc9jmQezLzq6PHPFgr8xDfjFiUxHc//PU6jFN7afW/YoldSnjYf0r45j
jQ/mlHxEc/u5cBXawjpK39oeytcfJHnxauuQMHMbW/YowrPHdSWHsji/0ftkntNOXu1/Ofu+bSG+
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
RU5ErkJggg==
--xyz--"""


def main():
    rcpt_to = "Ultimate95@mail.ru Savihev95@gmail.com"
    # s = SMTP("smtp.mail.ru", 587, "Rick_Grimes72@mail.ru", "123test")
    # s.send_mail_TLS()
    # test = s.get_only_images_base64("/home/savi/Рабочий стол/Интернет/Tasks/SMTP_mime/Pictures")
    # for key in test:
    #     print(test[key])
    #     print(key)
    # s.send_mail()
    # s.connect_tls()
    # s = SMTP_SSL("smtp.gmail.com", 587, "login", "password")
    # s = SMTP("127.0.0.1", 25, 'type_security', 'log', 'pass')
    # s.connect()
    # s.ehlo()
    # print(data)
    simple_socket("smtp.mail.ru", 587, "Rick_Grimes72@mail.ru", "123test", rcpt_to)
    # simple_socket("smtp.mail.ru", 465, "Rick_Grimes72@mail.ru", "123test1")

if __name__ == "__main__":
    main()

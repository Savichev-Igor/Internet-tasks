# !/usr/bin/python2
# -*- coding: utf-8 -*-
import sys
import os
import requests
import argparse
import click
import getpass

from moduls.vk_appl_auth import VKAppAuth  # python2 only


def createParser():
    """Типичный аргпарсер"""
    parser = argparse.ArgumentParser(
            prog="python2 vk_api.py",
            description="""Hi, this script takes all photos from chosed album
                           VK in best quality. Run program one more time with only one parametr - run
                           for start.
                           (It works only on python2, also you must install all dependencies)
                        """,
            epilog="""(c) Savi, 2015. The author assumes no responsibility,
                      like always.
                   """
            )
    parser.add_argument("run", type=str,
                        help="Just for run")
    return parser


class VK_photo:

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.uid = None
        self.aid = None
        self.title = None
        self.access_token = None
        self.app_id = 4392739
        self.scope = 'photos'

    def auth(self):
        """Авторизация при помощи логина и пароля.
        После получение токена и айди юзера"""
        try:
            self.access_data = VKAppAuth().auth(self.login,
                                                self.password,
                                                self.app_id, self.scope)
            print("\nAuth is success\n")
            self.uid = self.access_data["user_id"]
            self.access_token = self.access_data["access_token"]
        except Exception:
            print("\nSomething is wrong...\n")
            sys.exit()

    def get_albums(self):
        """Получение всех альбомов пользователя, включая скрытые и системные"""
        query = "https://api.vk.com/method/{0}?owner_id={1}&need_system=1&access_token={2}".format("photos.getAlbums",
                                                                                                   self.uid,
                                                                                                   self.access_token)
        response = requests.post(query)
        return response.json()["response"]

    def select_album(self):
        """Выбираем конкретный альбом"""
        albums = self.get_albums()
        counter = 0
        list_albums = []
        for album in albums:
            print(str(counter) + ". " + album["title"])
            list_albums.append(album)
            counter += 1
        s_aid = input("\nYour choice (number): ")
        self.aid = list_albums[s_aid]["aid"]
        self.title = str(s_aid)

    def get_photos(self):
        """Получаем фоточки"""
        query = "https://api.vk.com/method/{0}?owner_id={1}&album_id={2}&access_token={3}".format("photos.get",
                                                                                                  self.uid,
                                                                                                  self.aid, self.access_token)
        response = requests.post(query)
        photos = response.json()["response"]
        counter = 1
        try:
            os.mkdir(self.title)
        except Exception:
            print("\nDir already exists\n")
        print("\nGetting photos...\n")
        with click.progressbar(photos) as bar:
            for photo in bar:
                with open(self.title + "/" + str(counter) + ".jpg", "wb") as f:
                    if photo.get("src_xxxbig"):
                        b = self.get_bytes(photo["src_xxxbig"])
                        f.write(b)
                    elif photo.get("src_xxbig"):
                        b = self.get_bytes(photo["src_xxbig"])
                        f.write(b)
                    elif photo.get("src_xbig"):
                        b = self.get_bytes(photo["src_xbig"])
                        f.write(b)
                    elif photo.get("src_big"):
                        b = self.get_bytes(photo["src_big"])
                        f.write(b)
                counter += 1
        print("\nYou can check dir :)\n")

    def get_bytes(self, url):
        """Байты фоточек"""
        resource = requests.get(url)
        return resource.content


def create_obj():
    """Пытаемся создать наш API object"""
    login = raw_input("\nYour login: ")
    password = getpass.getpass(prompt="\nYour password: ")
    V = VK_photo(login, password)
    return V


def main():
    """Без комментариев"""
    try:
        p = createParser()
        a = p.parse_args()
        if a.run == "run":
            flag = True
            while flag:
                V_obj = create_obj()
                try:
                    V_obj.auth()
                    flag = False
                except:
                    print("You did mistake in login or password")
            V_obj.select_album()
            V_obj.get_photos()
        if len(sys.argv) == 1 or len(sys.argv) > 2:
            p.print_help()
    except Exception:
        print("\nSomething is wrong :<\n")
        sys.exit()

if __name__ == "__main__":
    main()

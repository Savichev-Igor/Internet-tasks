# !/usr/bin/python2
# -*- coding: utf-8 -*-
import sys
import os
import urllib
import click    # for good loking :>
import getpass  # Security :3
import argparse
import vkontakte    # API python2 only


from moduls.vk_appl_auth import VKAppAuth   # python2 only


def createParser():
    parser = argparse.ArgumentParser(
            prog='python2 vk_api.py',
            description="""Hi, this script takes all photos from chosed album
                           VK in best quality. Run program one more time with only one parametr - run
                           for start.
                        """,
            epilog="""(c) Savi, 2015. The author assumes no responsibility,
                      like always.
                   """
            )
    parser.add_argument('run', type=str,
                        help="Just for run")
    return parser


class VK_photo:

    def __init__(self, email, password, album_name):
        self.app_id = 4392739
        self.scope = 'photos'
        self.email = email
        self.password = password
        self.album_name = album_name
        self.id = None
        self.aid = None

    def auth(self):
        try:
            self.access_data = VKAppAuth().auth(self.email,
                                                self.password,
                                                self.app_id, self.scope)
            print('\nAuth is success\n')
        except Exception as er:
            print(er)
            print("\nSomething is wrong...\n")
            sys.exit()

        self.vk = vkontakte.API(token=self.access_data["access_token"])
        self.id = self.access_data['user_id']

    def get_albums(self):
        albums = self.vk.photos.getAlbums(owner_id=self.id)
        for album in albums:
            if album['title'] == self.album_name:
                self.aid = album['aid']
        if self.aid:
            pass
        else:
            print("\nWe can't find {0} album".format(self.album_name))
            sys.exit()

    def get_photos(self):
        photos = self.vk.photos.get(owner_id=self.id, album_id=self.aid)
        counter = 1
        try:
            os.mkdir(self.album_name)
        except Exception as er:
            # print(er)
            print('\nDir already exists\n')
        print('\nGetting photos...\n')
        with click.progressbar(photos) as bar:
            for photo in bar:
                with open(self.album_name + '/' +str(counter)+'.jpg', 'wb') as f:
                    if photo.has_key('src_xxxbig'):
                        b = self.get_bytes(photo['src_xxxbig'])
                        f.write(b)
                    elif photo.has_key('src_xxbig'):
                        b = self.get_bytes(photo['src_xxbig'])
                        f.write(b)
                    elif photo.has_key('src_xbig'):
                        b = self.get_bytes(photo['src_xbig'])
                        f.write(b)
                    elif photo.has_key('src_big'):
                        b = self.get_bytes(photo['src_big'])
                        f.write(b)
                counter += 1
        print('\nYou can check dir :)\n')

    def get_bytes(self, url):
        resource = urllib.urlopen(url)
        return resource.read()


def main():
    try:
        p = createParser()
        a = p.parse_args()
        if a.run == 'run':
            sys.stdout.write('\nYour login: ')
            login = raw_input()
            sys.stdout.write('\nYour pass: ')
            password = getpass.getpass()
            sys.stdout.write("\nAlbum's name: ")
            album_name = raw_input()
            v = VK_photo(login, password, album_name)
            v.auth()
            v.get_albums()
            v.get_photos()
        elif len(sys.argv) >= 1:
            p.print_help()
    except Exception as er:
        print(er)
        print('\n:<\n')
        sys.exit()

if __name__ == "__main__":
    main()

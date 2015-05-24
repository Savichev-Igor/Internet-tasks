# !/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import requests
import argparse
import click


def createParser():
    parser = argparse.ArgumentParser(
            prog='python3 vk_api.py',
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

    def __init__(self, user_id, album_name):
        self.id = user_id
        self.album_name = album_name
        self.aid = None

    def get_albums(self):
        query = 'https://api.vk.com/method/{0}?owner_id={1}'.format('photos.getAlbums', self.id)
        response = requests.post(query)
        return response.json()['response']

    def get_album(self):
        albums = self.get_albums()
        for album in albums:
            if album['title'] == self.album_name:
                self.aid = album['aid']
        if self.aid:
            pass
        else:
            print("\nWe can't find {0} album".format(self.album_name))
            sys.exit()

    def get_photos(self):
        query = 'https://api.vk.com/method/{0}?owner_id={1}&album_id={2}'.format('photos.get', self.id, self.aid)
        response = requests.post(query)
        photos = response.json()['response']
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
                    if photo.get('src_xxxbig'):
                        b = self.get_bytes(photo['src_xxxbig'])
                        f.write(b)
                    elif photo.get('src_xxbig'):
                        b = self.get_bytes(photo['src_xxbig'])
                        f.write(b)
                    elif photo.get('src_xbig'):
                        b = self.get_bytes(photo['src_xbig'])
                        f.write(b)
                    elif photo.get('src_big'):
                        b = self.get_bytes(photo['src_big'])
                        f.write(b)
                counter += 1
        print('\nYou can check dir :)\n')

    def get_bytes(self, url):
        resource = requests.get(url)
        return resource.content


def get_input():
    print("\nIs it group or user ? (g/u): ", end='')
    flag = input()
    if flag == 'g' or flag == 'u':
        print("\nid: ", end='')
        inp_id = input()
        if flag == 'g':
            inp_id = '-' + inp_id
        print("\nAlbum's name: ", end='')
        album_name = input()
        return inp_id, album_name
    else:
        get_input()


def main():
    try:
        p = createParser()
        a = p.parse_args()
        if a.run == 'run':
            inp = get_input()
            V = VK_photo(inp[0], inp[1])
            V.get_album()
            V.get_photos()
        elif len(sys.argv) >= 1:
            p.print_help()
    except Exception as er:
        # print(er)
        print('\nSomething is wrong :<\n')
        sys.exit()

if __name__ == "__main__":
    main()

# !/usr/bin/python2
# -- coding: utf-8 --
import cookielib
import urllib2
import urllib
from urlparse import urlparse

from moduls.vk_forms_parser import FormParser


class VKAppAuth():

    def auth_user(self, email, password, client_id, scope, opener):

        response = opener.open(
            "https://oauth.vk.com/oauth/authorize?" +\
            "redirect_uri=https://oauth.vk.com/blank.html&response_type=token&" +\
            "client_id=%s&scope=%s&display=wap" % (client_id, ",".join(scope))
            )
        html = response.read()

        parser = FormParser()
        parser.feed(html)
        parser.close()

        if not parser.form_parsed or parser.url is None or "pass" not in parser.params or \
        "email" not in parser.params:
                raise RuntimeError("Something wrong with a parser. Unable parse VK authorization form.")

        parser.params["email"] = email
        parser.params["pass"] = password

        if parser.method == "post":
            response = opener.open(parser.url, urllib.urlencode(parser.params))
        else:
            raise NotImplementedError("Method '%s'" % parser.params.method % " for user authorization form \
                submission is currently not supported. Please implement it if there is a need.")
        return response.read(), response.geturl()

    def give_access(self, html, opener):

        parser = FormParser()
        parser.feed(html)
        parser.close()

        if not parser.form_parsed or parser.url is None:
                raise RuntimeError("Something wrong with a parser. Unable parse VK application authorization form.")

        if parser.method == "post":
            response = opener.open(parser.url, urllib.urlencode(parser.params))
        else:
            raise NotImplementedError("Form method '%s'" % parser.params.method + "for application authorization \
            form submission is currently not supported. Please implement it if there is a need.")

        return response.geturl()

    def auth(self, email, password, app_id, scope):

        if not isinstance(scope, list):
            scope = [scope]

        opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
            urllib2.HTTPRedirectHandler())

        html, url = self.auth_user(email, password, app_id, scope, opener)

        if urlparse(url).path != "/blank.html":
            url = self.give_access(html, opener)

        if urlparse(url).path != "/blank.html":
            raise RuntimeError("Bad responce from oauth server. An error occured by obtaining access_token.")

        def split_key_value(kv_pair):
            kv = kv_pair.split("=")
            return kv[0], kv[1]

        answer = dict(split_key_value(kv_pair) for kv_pair in urlparse(url).fragment.split("&"))
        if "access_token" not in answer or "user_id" not in answer or "expires_in" not in answer:
            raise RuntimeError("Missing access token or users id values in answer.")
        return {"access_token": answer["access_token"], "user_id": answer["user_id"], "expires_in": answer["expires_in"]}

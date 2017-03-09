#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GENRE_NAME = 'hip-hop'

def genre_key(genre_name=DEFAULT_GENRE_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Genre', genre_name)

def cart_key(cart_email):
    return ndb.Key('Cart', cart_email)

class Song(ndb.Model):
    """A main model for representing an individual Song entry."""
    artist = ndb.StringProperty()
    title = ndb.StringProperty()
    price = ndb.IntegerProperty()
    album = ndb.StringProperty(indexed=False)

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
# [END main_page]

# [START enter]
class Enter(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE_NAME)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'genre_name': urllib.quote_plus(genre_name),
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('enter.html')
        self.response.write(template.render(template_values))

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        genre_name = self.request.get('genre_name',
                                          DEFAULT_GENRE_NAME)
        song = Song(parent=genre_key(genre_name))

        song.artist = self.request.get('artist')
        song.title = self.request.get('song_title')
        song.album = self.request.get('album')
        song.price = int(self.request.get('price'))

        song.put()

        self.redirect('/enter?genre_name=' + genre_name)
# [END enter]

# [START browse]
class Browse(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name',
                                          DEFAULT_GENRE_NAME)
        songs_query = Song.query(
            ancestor=genre_key(genre_name)).order(Song.artist)
        songs = songs_query.fetch()

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'songs': songs,
            'genre_name': urllib.quote_plus(genre_name)
        }

        template = JINJA_ENVIRONMENT.get_template('browse.html')
        self.response.write(template.render(template_values))

    def post(self):

        genre_name = self.request.get('genre_name',
                                          DEFAULT_GENRE_NAME)
        if self.request.get('song_to_cart_artist'):
            user = users.get_current_user()
            if user:
                song_add = Song(parent=cart_key(user.email()))

                song_add.artist = self.request.get('song_to_cart_artist')
                song_add.title = self.request.get('song_to_cart_title')
                song_add.album = self.request.get('song_to_cart_album')
                song_add.price = int(self.request.get('song_to_cart_price'))
                song_add.put()
            else:
                # if not login, first login then add to cart
                # after sign in, redirect to original search result
                self.redirect(users.create_login_url('/browse?genre_name=' + genre_name))
                return
        self.redirect('/browse?genre_name=' + genre_name)
# [END browse]

# [START search]
class Search(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE_NAME)
        art = self.request.get('artist')

        songs_query = Song.query(
            ancestor=genre_key(genre_name)).order(-Song.title)
        #songs_temp = ndb.GqlQuery("SELECT * FROM songs_query WHERE artist =~ art_temp")
        songs = []
        if art:
            for song in songs_query.fetch():
                if art.lower() in song.artist.lower():
                    songs.append(song)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'artist': art,
            'songs': songs,
            'genre_name': urllib.quote_plus(genre_name)
        }

        template = JINJA_ENVIRONMENT.get_template('search.html')
        self.response.write(template.render(template_values))

    def post(self):
        genre_name = self.request.get('genre_name',
                                          DEFAULT_GENRE_NAME)
        artist = self.request.get('artist')

        if self.request.get('song_to_cart_artist'):
            user = users.get_current_user()
            if user:
                song_add = Song(parent=cart_key(user.email()))

                song_add.artist = self.request.get('song_to_cart_artist')
                song_add.title = self.request.get('song_to_cart_title')
                song_add.album = self.request.get('song_to_cart_album')
                song_add.price = int(self.request.get('song_to_cart_price'))
                song_add.put()
            else:
                # if not login, first login then add to cart
                # after sign in, redirect to original search result
                self.redirect(users.create_login_url('/search?genre_name=' + genre_name + '&artist=' + artist))
                return

        print(users.get_current_user())

        self.redirect('/search?genre_name=' + genre_name + '&artist=' + artist)
# [END search]

# [START shopping cart]
class ShoppingCart(webapp2.RequestHandler):

    def get(self):
        if users.get_current_user():
            cart_email = users.get_current_user().email()
        else:
            self.redirect(users.create_login_url('/shoppingcart'))
            return
        cart_query = Song.query(ancestor=cart_key(cart_email)).order(Song.artist)
        songs = cart_query.fetch()

        template_values = {
            'songs': songs,
            'cart_email': cart_email
        }

        template = JINJA_ENVIRONMENT.get_template('shoppingcart.html')
        self.response.write(template.render(template_values))

    def post(self):
        if self.request.get('song_id'):
            user = users.get_current_user()
            if user:
                del_key_id = self.request.get('song_id')
                print(del_key_id)
                del_key = ndb.Key('Cart', user.email(), 'Song', int(del_key_id)) #have to use int to construct key id
                print(del_key)
                del_key.delete()
            else:
                # if not login, first login then add to cart
                # after sign in, redirect to original search result
                self.redirect(users.create_login_url('/shoppingcart'))
                return
        self.redirect('/shoppingcart')
# [END shopping cart]

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/enter', Enter),
    ('/browse', Browse),
    ('/search', Search),
    ('/shoppingcart', ShoppingCart),
], debug=True)
# [END app]

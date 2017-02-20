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


# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.

def genre_key(genre_name=DEFAULT_GENRE_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Genre', genre_name)

class Song(ndb.Model):
    """A main model for representing an individual Song entry."""
    artist = ndb.StringProperty()
    title = ndb.StringProperty()
    album = ndb.StringProperty(indexed=False)
# [END greeting]


# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
# [END main_page]
'''
class EnterPage(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE_NAME)

        template_values = {
            'genre_name': urllib.quote_plus(genre_name)
        }

        template = JINJA_ENVIRONMENT.get_template('enter.html')
        self.response.write(template.render(template_values))
'''
# [START enter]
class Enter(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE_NAME)

        template_values = {
            'genre_name': urllib.quote_plus(genre_name)
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

        template_values = {
            'songs': songs,
            'genre_name': urllib.quote_plus(genre_name)
        }

        template = JINJA_ENVIRONMENT.get_template('browse.html')
        self.response.write(template.render(template_values))
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

        template_values = {
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

        self.redirect('/search?genre_name=' + genre_name + '&artist=' + artist)
# [END search]

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/enter', Enter),
    ('/browse', Browse),
    ('/search', Search),
], debug=True)
# [END app]

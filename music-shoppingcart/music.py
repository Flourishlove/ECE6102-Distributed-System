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

class TotalCost(ndb.Model):
    cost = ndb.IntegerProperty()

class Purchased(ndb.Model):
    song_list = ndb.StructuredProperty(Song, repeated=True)
    date_time = ndb.DateTimeProperty(auto_now_add=True)
    total_cost = ndb.IntegerProperty()

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
        # We set the same parent key on the 'Song' to ensure each
        # song is in the same entity group. Queries across the
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

                cost_key = ndb.Key('TotalCost', user.email())
                if cost_key.get():
                    temp_cost = cost_key.get()
                    temp_cost.cost = temp_cost.cost + song_add.price
                    temp_cost.put()
                else:
                    cost_entity = TotalCost(cost=song_add.price)
                    cost_entity.key = cost_key
                    cost_entity.put()

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

                cost_key = ndb.Key('TotalCost', user.email())
                if cost_key.get():
                    temp_cost = cost_key.get()
                    temp_cost.cost = temp_cost.cost + song_add.price
                    temp_cost.put()
                else:
                    cost_entity = TotalCost(cost=song_add.price)
                    cost_entity.key = cost_key
                    cost_entity.put()

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
        user = users.get_current_user()
        if users.get_current_user():
            cart_email = users.get_current_user().email()
        else:
            self.redirect(users.create_login_url('/shoppingcart'))
            return
        cart_query = Song.query(ancestor=cart_key(cart_email)).order(Song.artist)
        songs = cart_query.fetch()

        cost_key = ndb.Key('TotalCost', user.email())
        if cost_key.get():
            temp_cost = cost_key.get().cost
        else:
            temp_cost = 0

        template_values = {
            'songs': songs,
            'total_cost': temp_cost,
            'cart_email': cart_email
        }

        template = JINJA_ENVIRONMENT.get_template('shoppingcart.html')
        self.response.write(template.render(template_values))

    def post(self):
        user = users.get_current_user()
        cost_key = ndb.Key('TotalCost', user.email())
        temp_cost = cost_key.get()

        if self.request.get('song_del_id'):
            if user:
                del_key_id = self.request.get('song_del_id')
                del_key = ndb.Key('Cart', user.email(), 'Song', int(del_key_id)) #have to use int to construct key id

                temp_cost.cost = temp_cost.cost - del_key.get().price
                temp_cost.put()

                del_key.delete()

            else:
                # if not login, first login then add to cart
                # after sign in, redirect to original search result
                self.redirect(users.create_login_url('/shoppingcart'))
                return
        if self.request.get('purchase'):
            cart_songs = Song.query(ancestor=cart_key(user.email())).fetch()
            for cart_song in cart_songs:
                temp_cost.cost = temp_cost.cost - cart_song.price
                temp_cost.put()
                cart_song.key.delete()

        self.redirect('/shoppingcart')
# [END shopping cart]

# [start purchase]
class Purchase(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        cost_key = ndb.Key('TotalCost', user.email())
        temp_cost = cost_key.get()

        purchased = Purchased(parent=cart_key(user.email()))
        purchased.total_cost = 0

        cart_songs = Song.query(ancestor=cart_key(user.email())).fetch()
        for cart_song in cart_songs:
            temp_cost.cost = temp_cost.cost - cart_song.price
            temp_cost.put()

            song = Song(parent=cart_key(user.email()))
            song.artist = cart_song.artist
            song.title = cart_song.title
            song.album = cart_song.album
            song.price = cart_song.price

            purchased.song_list.append(song)
            purchased.total_cost = purchased.total_cost + cart_song.price
            purchased.put()
            cart_song.key.delete()

        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template('purchased.html')
        self.response.write(template.render(template_values))
# [END purchase]

# [start purchase history]
class History(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        purchased_history = Purchased.query(ancestor=cart_key(user.email())).fetch()
        template_values = {
            'purchased_history': purchased_history,
            'cart_email': user.email()
        }

        template = JINJA_ENVIRONMENT.get_template('history.html')
        self.response.write(template.render(template_values))

# [END purchase history]

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/enter', Enter),
    ('/browse', Browse),
    ('/search', Search),
    ('/shoppingcart', ShoppingCart),
    ('/purchase', Purchase),
    ('/history', History)
], debug=True)
# [END app]
